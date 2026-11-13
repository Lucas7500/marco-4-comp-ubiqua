import json
from unittest.mock import Mock

from conftest import ClientFactory

from constants import ACTUATOR_CHANNEL_ID, SENSOR_CHANNEL_ID
from models.contracts import Reading


def test_mqtt_callback_to_two_websockets_and_shutdown(
    client_for: ClientFactory,
    sensor_payload: dict[str, object],
    expected_sensor: Reading,
) -> None:
    with client_for() as client:
        live = client.app.state.live
        with client.websocket_connect("/api/v1/ws/readings") as first:
            with client.websocket_connect("/api/v1/ws/readings") as second:
                live.on_message(
                    None,
                    None,
                    Mock(
                        topic=f"channels/{SENSOR_CHANNEL_ID}/subscribe",
                        payload=json.dumps(sensor_payload).encode(),
                    ),
                )
                assert first.receive_json() == second.receive_json() == expected_sensor
            live.on_message(
                None,
                None,
                Mock(
                    topic=f"channels/{ACTUATOR_CHANNEL_ID}/subscribe",
                    payload=b'{"field1":"1"}',
                ),
            )
            assert first.receive_json() == {
                "channel_id": ACTUATOR_CHANNEL_ID,
                "fields": {"field1": 1},
            }
        assert not live.sockets
    assert not live.tasks and not live.sockets and live.stopping
    assert client.app.state.http.is_closed
