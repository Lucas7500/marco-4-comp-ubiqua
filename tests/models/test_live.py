import asyncio
import json
from http import HTTPStatus
from unittest.mock import AsyncMock, Mock

import pytest
from conftest import ClientFactory
from starlette import status
from starlette.websockets import WebSocketDisconnect

from config import CHANNELS, Settings
from constants import (
    ACTUATOR_CHANNEL_ID,
    MQTT_KEEPALIVE_SECONDS,
    MQTT_SUBSCRIPTION_QOS,
    MQTT_TLS_PORT,
    SENSOR_CHANNEL_ID,
)
from models.contracts import Reading
from models.live import Live

MQTT_CONNECTION_COUNT: int = 2
ASYNC_TEST_TIMEOUT_SECONDS: int = 1


@pytest.fixture
def mqtt_client(monkeypatch: pytest.MonkeyPatch) -> Mock:
    client = Mock()
    monkeypatch.setattr("models.live.mqtt.Client", Mock(return_value=client))
    return client


def test_mqtt_reconnect_subscribes_and_stops(
    mqtt_client: Mock, client_for: ClientFactory
) -> None:
    mqtt = mqtt_client
    settings = Settings(client_id="test", username="test", password="test")
    with client_for(settings=settings) as client:
        live = client.app.state.live
        mqtt.username_pw_set.assert_called_once_with("test", "test")
        mqtt.tls_set.assert_called_once_with()
        mqtt.connect_async.assert_called_once_with(
            "mqtt3.thingspeak.com", MQTT_TLS_PORT, MQTT_KEEPALIVE_SECONDS
        )
        mqtt.loop_start.assert_called_once_with()
        for _ in range(MQTT_CONNECTION_COUNT):
            live.on_connect(mqtt, None, None, Mock(is_failure=False), None)
        expected_subscription_count = MQTT_CONNECTION_COUNT * len(CHANNELS)
        assert mqtt.subscribe.call_count == expected_subscription_count
        mqtt.subscribe.assert_any_call(
            f"channels/{SENSOR_CHANNEL_ID}/subscribe", qos=MQTT_SUBSCRIPTION_QOS
        )
        mqtt.subscribe.assert_any_call(
            f"channels/{ACTUATOR_CHANNEL_ID}/subscribe", qos=MQTT_SUBSCRIPTION_QOS
        )
        assert client.get("/health").status_code == HTTPStatus.OK
    mqtt.disconnect.assert_called_once()
    mqtt.loop_stop.assert_called_once()


@pytest.mark.parametrize(
    "error", [OSError, RuntimeError, asyncio.TimeoutError, WebSocketDisconnect]
)
@pytest.mark.parametrize("close_fails", [False, True])
def test_disconnected_socket_does_not_break_broadcast(
    error: type[Exception], close_fails: bool
) -> None:
    async def check() -> None:
        live = Live(Settings())
        broken = Mock(send_json=AsyncMock(side_effect=error()))
        broken.close = AsyncMock(side_effect=error() if close_fails else None)
        healthy = Mock(send_json=AsyncMock())
        live.sockets.update([broken, healthy])
        event: Reading = {"channel_id": SENSOR_CHANNEL_ID, "fields": {"field1": 28.5}}
        await live.broadcast(event)
        assert live.sockets == {healthy}
        healthy.send_json.assert_awaited_once_with(event)
        broken.close.assert_awaited_once_with(code=status.WS_1011_INTERNAL_ERROR)

    asyncio.run(check())


def test_mqtt_message_before_start_is_ignored(
    sensor_payload: dict[str, object],
) -> None:
    live = Live(Settings())
    live.on_message(
        None,
        None,
        Mock(
            topic=f"channels/{SENSOR_CHANNEL_ID}/subscribe",
            payload=json.dumps(sensor_payload).encode(),
        ),
    )
    assert not live.tasks


def test_rejected_mqtt_connection_does_not_subscribe(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = Mock()
    Live(Settings()).on_connect(client, None, None, Mock(is_failure=True), None)
    client.subscribe.assert_not_called()
    assert "Conexão MQTT recusada" in caplog.text


@pytest.mark.parametrize("failure", [False, True])
def test_subscription_acknowledgement(
    failure: bool, caplog: pytest.LogCaptureFixture
) -> None:
    Live(Settings()).on_subscribe(None, None, 1, [Mock(is_failure=failure)], None)
    assert ("Assinatura MQTT recusada" in caplog.text) is failure


@pytest.mark.parametrize(
    "topic,payload",
    [
        (f"channels/{SENSOR_CHANNEL_ID}/subscribe", b"broken"),
        (f"channels/{SENSOR_CHANNEL_ID}/subscribe", b"[]"),
        (f"channels/{SENSOR_CHANNEL_ID}/subscribe", b'{"field1":true}'),
        (f"channels/{SENSOR_CHANNEL_ID}/subscribe", b"\xff"),
        ("channels/9/subscribe", b'{"field1":"1"}'),
    ],
)
def test_invalid_mqtt_messages_are_not_scheduled(
    topic: str, payload: bytes, caplog: pytest.LogCaptureFixture
) -> None:
    live = Live(Settings())
    live.loop = Mock()
    live.on_message(None, None, Mock(topic=topic, payload=payload))
    live.loop.call_soon_threadsafe.assert_not_called()
    assert "Mensagem MQTT inválida descartada" in caplog.text


def test_mqtt_callback_tolerates_closed_loop(sensor_payload: dict[str, object]) -> None:
    live = Live(Settings())
    live.loop = Mock()
    live.loop.call_soon_threadsafe.side_effect = RuntimeError("Event loop is closed")
    live.on_message(
        None,
        None,
        Mock(
            topic=f"channels/{SENSOR_CHANNEL_ID}/subscribe",
            payload=json.dumps(sensor_payload).encode(),
        ),
    )
    live.loop.call_soon_threadsafe.assert_called_once()
    assert not live.tasks


def test_shutdown_cancels_pending_broadcast_and_prevents_new_tasks() -> None:
    async def check() -> None:
        live = Live(Settings())
        started = asyncio.Event()

        async def blocked_send(event: Reading) -> None:
            started.set()
            await asyncio.Event().wait()

        live.sockets.add(Mock(send_json=blocked_send))
        event: Reading = {"channel_id": SENSOR_CHANNEL_ID, "fields": {}}
        live.schedule(event)
        await asyncio.wait_for(started.wait(), timeout=ASYNC_TEST_TIMEOUT_SECONDS)
        pending = tuple(live.tasks)
        await live.stop()
        assert all(task.cancelled() for task in pending)
        assert not live.tasks
        assert not live.sockets
        live.schedule(event)
        assert not live.tasks

    asyncio.run(check())
