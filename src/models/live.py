import asyncio
import json
import logging

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode
from starlette import status
from starlette.websockets import WebSocket, WebSocketDisconnect

from config import CHANNELS, Settings
from constants import MQTT_KEEPALIVE_SECONDS, MQTT_SUBSCRIPTION_QOS, MQTT_TLS_PORT
from models.contracts import Reading
from utils.reading_normalizer import ReadingNormalizer

logger: logging.Logger = logging.getLogger(__name__)

MQTT_MIN_RECONNECT_DELAY_SECONDS: int = 1
MQTT_MAX_RECONNECT_DELAY_SECONDS: int = 30
WEBSOCKET_SEND_TIMEOUT_SECONDS: int = 5
WEBSOCKET_CLOSE_TIMEOUT_SECONDS: int = 1


class Live:
    def __init__(self, settings: Settings) -> None:
        self.settings: Settings = settings
        self.sockets: set[WebSocket] = set()
        self.tasks: set[asyncio.Task[None]] = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.client: mqtt.Client | None = None
        self.stopping: bool = False

    def start(self) -> None:
        self.loop = asyncio.get_running_loop()
        if not self.settings.client_id:
            logger.warning("MQTT desabilitado: credenciais ausentes")
            return
        self.client = mqtt.Client(
            CallbackAPIVersion.VERSION2, client_id=self.settings.client_id
        )
        self.client.username_pw_set(self.settings.username, self.settings.password)
        self.client.tls_set()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.reconnect_delay_set(
            MQTT_MIN_RECONNECT_DELAY_SECONDS, MQTT_MAX_RECONNECT_DELAY_SECONDS
        )
        self.client.connect_async(
            "mqtt3.thingspeak.com", MQTT_TLS_PORT, MQTT_KEEPALIVE_SECONDS
        )
        self.client.loop_start()

    def on_connect(
        self,
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags | None,
        reason_code: ReasonCode,
        properties: Properties | None,
    ) -> None:
        if reason_code.is_failure:
            logger.warning("Conexão MQTT recusada")
            return
        for channel_id in CHANNELS:
            client.subscribe(
                f"channels/{channel_id}/subscribe", qos=MQTT_SUBSCRIPTION_QOS
            )

    def on_subscribe(
        self,
        client: mqtt.Client | None,
        userdata: object,
        mid: int,
        reason_codes: list[ReasonCode],
        properties: Properties | None,
    ) -> None:
        if any(code.is_failure for code in reason_codes):
            logger.warning("Assinatura MQTT recusada; confira permissões do Device")

    def on_message(
        self, client: mqtt.Client | None, userdata: object, message: mqtt.MQTTMessage
    ) -> None:
        try:
            topics = {f"channels/{c}/subscribe": c for c in CHANNELS}
            event = ReadingNormalizer(topics[message.topic]).normalize(
                json.loads(message.payload)
            )
        except (ValueError, TypeError, KeyError, OverflowError, UnicodeError):
            logger.warning("Mensagem MQTT inválida descartada")
            return
        if not self.stopping and self.loop is not None:
            try:
                self.loop.call_soon_threadsafe(self.schedule, event)
            except RuntimeError:
                pass  # O loop pode terminar enquanto o callback finaliza.

    def schedule(self, event: Reading) -> None:
        if not self.stopping:
            task = asyncio.create_task(self.broadcast(event))
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)

    async def broadcast(self, event: Reading) -> None:
        async def send(socket: WebSocket) -> None:
            try:
                await asyncio.wait_for(
                    socket.send_json(event), timeout=WEBSOCKET_SEND_TIMEOUT_SECONDS
                )
            except (TimeoutError, OSError, RuntimeError, WebSocketDisconnect):
                self.sockets.discard(socket)
                try:
                    await asyncio.wait_for(
                        socket.close(code=status.WS_1011_INTERNAL_ERROR),
                        timeout=WEBSOCKET_CLOSE_TIMEOUT_SECONDS,
                    )
                except (TimeoutError, OSError, RuntimeError, WebSocketDisconnect):
                    pass

        await asyncio.gather(*(send(socket) for socket in tuple(self.sockets)))

    async def stop(self) -> None:
        self.stopping = True
        if self.client:
            self.client.disconnect()
            await asyncio.to_thread(self.client.loop_stop)
        for task in tuple(self.tasks):
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        self.sockets.clear()
