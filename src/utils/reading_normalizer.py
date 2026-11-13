import math

from config import CHANNELS
from constants import ACTUATOR_CHANNEL_ID, ACTUATOR_OFF, ACTUATOR_ON
from models.contracts import FieldValue, Reading

MIN_ENTRY_ID: int = 1


class ReadingNormalizer:
    def __init__(self, channel_id: int) -> None:
        self.channel_id: int = channel_id

    def normalize(self, data: object) -> Reading:
        if not isinstance(data, dict):
            raise ValueError("Leitura inválida")  # noqa: TRY004 - Preserve the validation exception contract.
        fields = self._normalize_fields(data)
        result: Reading = {"channel_id": self.channel_id, "fields": fields}
        self._add_metadata(result, data)
        return result

    def _normalize_fields(self, data: dict[str, object]) -> dict[str, FieldValue]:
        if not any(k in data for k in CHANNELS[self.channel_id]["fields"]):
            raise ValueError("Leitura inválida")
        fields: dict[str, FieldValue] = {}
        for key in CHANNELS[self.channel_id]["fields"]:
            if key not in data:
                continue
            fields[key] = self._normalize_field_value(data[key])
        return fields

    def _normalize_field_value(self, value: object) -> FieldValue:
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ValueError("Campo inválido")
            number = float(value)
            if self.channel_id == ACTUATOR_CHANNEL_ID:
                if number not in (ACTUATOR_OFF, ACTUATOR_ON):
                    raise ValueError("Estado inválido")
                value = int(number)
            elif math.isfinite(number):
                value = number
            elif not isinstance(value, str):
                raise ValueError("Número JSON não finito")
            # O DHT pode publicar a string nan; preserve-a, sem inventar uma medição.
        return value

    @staticmethod
    def _add_metadata(result: Reading, data: dict[str, object]) -> None:
        entry_id = data.get("entry_id")
        if entry_id is not None:
            if type(entry_id) is not int or entry_id < MIN_ENTRY_ID:
                raise ValueError("entry_id inválido")
            result["entry_id"] = entry_id
        created_at = data.get("created_at")
        if created_at is not None:
            if not isinstance(created_at, str):
                raise ValueError("Timestamp inválido")
            result["created_at"] = created_at
