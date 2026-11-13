"""Mapeamento dos dois firmwares; nenhuma regra de controle é executada aqui."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from dotenv import dotenv_values

from constants import ACTUATOR_CHANNEL_ID, ACTUATOR_OFF, ACTUATOR_ON, SENSOR_CHANNEL_ID
from models.contracts import ChannelMetadata

CHANNELS: dict[int, ChannelMetadata] = {
    SENSOR_CHANNEL_ID: {
        "name": "Sensores",
        "fields": {
            "field1": {"name": "Temperatura", "unit": "°C", "type": "float"},
            "field2": {"name": "Umidade", "unit": "%", "type": "float"},
            "field3": {"name": "Gás inflamável", "unit": "PPM", "type": "float"},
        },
    },
    ACTUATOR_CHANNEL_ID: {
        "name": "Atuadores",
        "fields": {
            "field1": {
                "name": "Ar-condicionado",
                "type": "integer",
                "states": {ACTUATOR_OFF: "desligado", ACTUATOR_ON: "ligado"},
            },
            "field2": {
                "name": "Umidificador",
                "type": "integer",
                "states": {ACTUATOR_OFF: "desligado", ACTUATOR_ON: "ligado"},
            },
            "field3": {
                "name": "Ventilação",
                "type": "integer",
                "states": {ACTUATOR_OFF: "desligado", ACTUATOR_ON: "ligado"},
            },
        },
    },
}


@dataclass
class Settings:
    read_keys: dict[int, str] = field(default_factory=dict, repr=False)
    client_id: str = field(default="", repr=False)
    username: str = field(default="", repr=False)
    password: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        if set(self.read_keys) - CHANNELS.keys():
            raise ValueError("Canal não identificado no firmware")
        credentials = (self.client_id, self.username, self.password)
        if any(credentials) and not all(credentials):
            raise ValueError("Preencha as três credenciais MQTT Device")

    @classmethod
    def load(cls) -> Self:
        project_root = Path(__file__).resolve().parent.parent
        values = {**dotenv_values(project_root / ".env"), **os.environ}
        return cls(
            read_keys={
                c: values.get(f"THINGSPEAK_READ_KEY_{c}") or "" for c in CHANNELS
            },
            client_id=values.get("THINGSPEAK_MQTT_CLIENT_ID") or "",
            username=values.get("THINGSPEAK_MQTT_USERNAME") or "",
            password=values.get("THINGSPEAK_MQTT_PASSWORD") or "",
        )
