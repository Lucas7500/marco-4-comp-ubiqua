import pytest

from constants import ACTUATOR_CHANNEL_ID, SENSOR_CHANNEL_ID
from utils.reading_normalizer import ReadingNormalizer


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"field1": True},
        {"field1": []},
        {"field1": "broken"},
        {"field1": float("nan")},
        {"field1": float("inf")},
        {"field1": "1", "entry_id": 0},
        {"field1": "1", "entry_id": True},
        {"field1": "1", "entry_id": "7"},
        {"field1": "1", "created_at": 123},
    ],
    ids=[
        "not-object",
        "no-fields",
        "boolean",
        "list",
        "non-numeric",
        "numeric-nan",
        "numeric-infinity",
        "zero-id",
        "boolean-id",
        "string-id",
        "numeric-timestamp",
    ],
)
def test_normalization_rejects_invalid_readings(payload: object) -> None:
    with pytest.raises(ValueError):
        ReadingNormalizer(SENSOR_CHANNEL_ID).normalize(payload)


def test_normalization_omits_null_metadata_and_unknown_fields() -> None:
    assert ReadingNormalizer(SENSOR_CHANNEL_ID).normalize(
        {
            "field1": "1",
            "field8": "2",
            "entry_id": None,
            "created_at": None,
        }
    ) == {"channel_id": SENSOR_CHANNEL_ID, "fields": {"field1": 1.0}}


def test_normalization_preserves_actuator_types_and_missing_fields() -> None:
    assert ReadingNormalizer(ACTUATOR_CHANNEL_ID).normalize(
        {"field1": "0", "field2": "1"}
    ) == {
        "channel_id": ACTUATOR_CHANNEL_ID,
        "fields": {"field1": 0, "field2": 1},
    }


def test_normalization_preserves_nan_string_and_null() -> None:
    assert ReadingNormalizer(SENSOR_CHANNEL_ID).normalize(
        {"field1": "nan", "field2": None}
    ) == {
        "channel_id": SENSOR_CHANNEL_ID,
        "fields": {"field1": "nan", "field2": None},
    }


def test_normalization_rejects_invalid_actuator_state() -> None:
    with pytest.raises(ValueError):
        ReadingNormalizer(ACTUATOR_CHANNEL_ID).normalize({"field1": "2"})
