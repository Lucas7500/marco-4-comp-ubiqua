from pathlib import Path
from typing import TypedDict

import pytest

from config import Settings
from constants import ACTUATOR_CHANNEL_ID, SENSOR_CHANNEL_ID


class SettingsOverrides(TypedDict, total=False):
    read_keys: dict[int, str]
    client_id: str
    username: str
    password: str


@pytest.fixture
def settings_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    monkeypatch.setattr("config.dotenv_values", lambda path: values)
    for key in (
        f"THINGSPEAK_READ_KEY_{SENSOR_CHANNEL_ID}",
        f"THINGSPEAK_READ_KEY_{ACTUATOR_CHANNEL_ID}",
        "THINGSPEAK_MQTT_CLIENT_ID",
        "THINGSPEAK_MQTT_USERNAME",
        "THINGSPEAK_MQTT_PASSWORD",
    ):
        monkeypatch.delenv(key, raising=False)
    return values


@pytest.mark.parametrize(
    "values",
    [
        {"client_id": "test"},
        {"username": "test"},
        {"password": "test"},
        {"client_id": "test", "username": "test"},
        {"read_keys": {1: "test"}},
    ],
    ids=[
        "client-only",
        "username-only",
        "password-only",
        "missing-password",
        "unknown-channel",
    ],
)
def test_settings_reject_invalid_configuration(values: SettingsOverrides) -> None:
    with pytest.raises(ValueError):
        Settings(**values)


def test_settings_loads_root_env_from_another_working_directory(
    settings_env: dict[str, str | None], monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = Path(__file__).resolve().parent.parent / ".env"

    def load_env(path: Path) -> dict[str, str]:
        assert path == expected
        return {f"THINGSPEAK_READ_KEY_{SENSOR_CHANNEL_ID}": "test-file-key"}

    monkeypatch.setattr("config.dotenv_values", load_env)
    monkeypatch.chdir(Path(__file__).resolve().parent)
    assert Settings.load().read_keys[SENSOR_CHANNEL_ID] == "test-file-key"


@pytest.mark.parametrize("value", [None, ""], ids=["without-value", "empty"])
def test_load_normalizes_empty_file_values(
    settings_env: dict[str, str | None], value: str | None
) -> None:
    settings_env.update(
        {
            f"THINGSPEAK_READ_KEY_{SENSOR_CHANNEL_ID}": value,
            f"THINGSPEAK_READ_KEY_{ACTUATOR_CHANNEL_ID}": value,
            "THINGSPEAK_MQTT_CLIENT_ID": value,
            "THINGSPEAK_MQTT_USERNAME": value,
            "THINGSPEAK_MQTT_PASSWORD": value,
        }
    )
    assert Settings.load() == Settings(
        read_keys={SENSOR_CHANNEL_ID: "", ACTUATOR_CHANNEL_ID: ""}
    )


def test_load_defaults_when_no_values_are_configured(
    settings_env: dict[str, str | None],
) -> None:
    assert Settings.load() == Settings(
        read_keys={SENSOR_CHANNEL_ID: "", ACTUATOR_CHANNEL_ID: ""}
    )


@pytest.mark.parametrize("source", ["file", "process", "override"])
def test_load_all_credentials_and_process_precedence(
    settings_env: dict[str, str | None], monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    values = {
        f"THINGSPEAK_READ_KEY_{SENSOR_CHANNEL_ID}": "sensor-key",
        f"THINGSPEAK_READ_KEY_{ACTUATOR_CHANNEL_ID}": "actuator-key",
        "THINGSPEAK_MQTT_CLIENT_ID": "client-id",
        "THINGSPEAK_MQTT_USERNAME": "username",
        "THINGSPEAK_MQTT_PASSWORD": "password",
    }
    if source == "file":
        settings_env.update(values)
    else:
        if source == "override":
            settings_env.update({key: "file-value" for key in values})
        for key, value in values.items():
            monkeypatch.setenv(key, value)

    assert Settings.load() == Settings(
        read_keys={
            SENSOR_CHANNEL_ID: "sensor-key",
            ACTUATOR_CHANNEL_ID: "actuator-key",
        },
        client_id="client-id",
        username="username",
        password="password",
    )


def test_load_merges_file_and_process_values(
    settings_env: dict[str, str | None], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings_env.update(
        {
            f"THINGSPEAK_READ_KEY_{SENSOR_CHANNEL_ID}": "sensor-key",
            "THINGSPEAK_MQTT_CLIENT_ID": "client-id",
            "THINGSPEAK_MQTT_USERNAME": "username",
        }
    )
    monkeypatch.setenv(f"THINGSPEAK_READ_KEY_{ACTUATOR_CHANNEL_ID}", "actuator-key")
    monkeypatch.setenv("THINGSPEAK_MQTT_PASSWORD", "password")

    assert Settings.load() == Settings(
        read_keys={
            SENSOR_CHANNEL_ID: "sensor-key",
            ACTUATOR_CHANNEL_ID: "actuator-key",
        },
        client_id="client-id",
        username="username",
        password="password",
    )


def test_load_empty_process_values_override_file(
    settings_env: dict[str, str | None], monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in (
        f"THINGSPEAK_READ_KEY_{SENSOR_CHANNEL_ID}",
        f"THINGSPEAK_READ_KEY_{ACTUATOR_CHANNEL_ID}",
        "THINGSPEAK_MQTT_CLIENT_ID",
        "THINGSPEAK_MQTT_USERNAME",
        "THINGSPEAK_MQTT_PASSWORD",
    ):
        settings_env[key] = "file-value"
        monkeypatch.setenv(key, "")

    assert Settings.load() == Settings(
        read_keys={SENSOR_CHANNEL_ID: "", ACTUATOR_CHANNEL_ID: ""}
    )


@pytest.mark.parametrize("source", ["file", "process"])
@pytest.mark.parametrize("missing", ["CLIENT_ID", "USERNAME", "PASSWORD"])
def test_load_rejects_partial_mqtt_credentials(
    settings_env: dict[str, str | None],
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    missing: str,
) -> None:
    for name in ("CLIENT_ID", "USERNAME", "PASSWORD"):
        if name != missing:
            key = f"THINGSPEAK_MQTT_{name}"
            if source == "file":
                settings_env[key] = "test-value"
            else:
                monkeypatch.setenv(key, "test-value")

    with pytest.raises(ValueError, match="Preencha as três credenciais MQTT Device"):
        Settings.load()


def test_load_rejects_partial_credentials_after_empty_override(
    settings_env: dict[str, str | None], monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("CLIENT_ID", "USERNAME", "PASSWORD"):
        settings_env[f"THINGSPEAK_MQTT_{name}"] = "file-value"
    monkeypatch.setenv("THINGSPEAK_MQTT_PASSWORD", "")

    with pytest.raises(ValueError, match="Preencha as três credenciais MQTT Device"):
        Settings.load()
