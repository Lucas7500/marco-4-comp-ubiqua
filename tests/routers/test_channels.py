from http import HTTPStatus

import httpx
import pytest
from conftest import ClientFactory
from fastapi.testclient import TestClient

from config import Settings
from constants import (
    ACTUATOR_CHANNEL_ID,
    DEFAULT_HISTORY_LIMIT,
    MAX_FIELD_NUMBER,
    MAX_HISTORY_LIMIT,
    MIN_FIELD_NUMBER,
    MIN_HISTORY_LIMIT,
    SENSOR_CHANNEL_ID,
)
from models.contracts import Reading


def test_catalog_does_not_access_network(client: TestClient) -> None:
    response = client.get("/api/v1/channels")
    assert response.status_code == HTTPStatus.OK
    channels = response.json()
    assert [item["channel_id"] for item in channels] == [
        SENSOR_CHANNEL_ID,
        ACTUATOR_CHANNEL_ID,
    ]
    assert channels[0]["fields"]["field1"]["unit"] == "°C"
    assert channels[1]["fields"]["field1"]["type"] == "integer"
    assert channels[1]["fields"]["field1"]["states"] == {
        "0": "desligado",
        "1": "ligado",
    }


def test_history_filters_and_private_key(
    client_for: ClientFactory, sensor_payload: dict[str, object]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/channels/{SENSOR_CHANNEL_ID}/feeds.json"
        assert request.url.params["results"] == "2"
        assert request.url.params["api_key"] == "test-only-key"
        assert request.url.params["start"] == "2026-01-01 03:00:00"
        assert request.url.params["end"] == "2026-01-02 00:00:00"
        return httpx.Response(
            HTTPStatus.OK,
            json={"channel": {"id": SENSOR_CHANNEL_ID}, "feeds": [sensor_payload]},
        )

    with client_for(
        handler, Settings(read_keys={SENSOR_CHANNEL_ID: "test-only-key"})
    ) as client:
        response = client.get(
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings",
            params={
                "limit": 2,
                "field": 1,
                "start": "2026-01-01T00:00:00-03:00",
                "end": "2026-01-02T00:00:00Z",
            },
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == [
            {
                "channel_id": SENSOR_CHANNEL_ID,
                "fields": {"field1": 28.5},
                "entry_id": 7,
                "created_at": "2026-01-01T10:00:00Z",
            }
        ]


def test_latest(
    client_for: ClientFactory,
    sensor_payload: dict[str, object],
    expected_sensor: Reading,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/feeds/last.json")
        return httpx.Response(HTTPStatus.OK, json=sensor_payload)

    with client_for(handler) as client:
        response = client.get(f"/api/v1/channels/{SENSOR_CHANNEL_ID}/latest")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_sensor


@pytest.mark.parametrize("body", ["null", "{}"], ids=["null", "empty-object"])
def test_latest_without_readings(client_for: ClientFactory, body: str) -> None:
    with client_for(lambda r: httpx.Response(HTTPStatus.OK, text=body)) as client:
        assert (
            client.get(f"/api/v1/channels/{SENSOR_CHANNEL_ID}/latest").status_code
            == HTTPStatus.NOT_FOUND
        )


@pytest.mark.parametrize(
    "path,expected_status",
    [
        ("/api/v1/channels/1/readings", HTTPStatus.NOT_FOUND),
        ("/api/v1/channels/1/latest", HTTPStatus.NOT_FOUND),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?limit={MIN_HISTORY_LIMIT - 1}",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?limit={MAX_HISTORY_LIMIT + 1}",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?field={MAX_FIELD_NUMBER + 1}",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?field={MIN_FIELD_NUMBER - 1}",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?limit=abc",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        ("/api/v1/channels/abc/latest", HTTPStatus.UNPROCESSABLE_ENTITY),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?end=2026-01-01",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?start=invalid",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?start=2026-01-01",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings?start=2026-02-01T00:00:00Z&end=2026-01-01T00:00:00Z",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
    ],
)
def test_invalid_input(
    path: str, expected_status: HTTPStatus, client_for: ClientFactory
) -> None:
    with client_for() as client:
        assert client.get(path).status_code == expected_status


@pytest.mark.parametrize(
    "error,expected_status",
    [
        (httpx.ReadTimeout, HTTPStatus.GATEWAY_TIMEOUT),
        (httpx.ConnectError, HTTPStatus.SERVICE_UNAVAILABLE),
    ],
)
@pytest.mark.parametrize("endpoint", ["latest", "readings"])
def test_network_errors(
    error: type[httpx.RequestError],
    expected_status: HTTPStatus,
    endpoint: str,
    client_for: ClientFactory,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error("sensitive upstream URL must not escape", request=request)

    with client_for(handler) as client:
        response = client.get(f"/api/v1/channels/{SENSOR_CHANNEL_ID}/{endpoint}")
        assert response.status_code == expected_status
        assert "sensitive" not in response.text


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(HTTPStatus.FORBIDDEN),
        httpx.Response(HTTPStatus.INTERNAL_SERVER_ERROR),
        httpx.Response(HTTPStatus.OK, text="not json"),
        httpx.Response(HTTPStatus.OK, json=-1),
        httpx.Response(HTTPStatus.OK, json={"feeds": []}),
        httpx.Response(HTTPStatus.OK, json={"channel": {"id": 1}, "feeds": []}),
        httpx.Response(
            HTTPStatus.OK,
            json={
                "channel": {"id": SENSOR_CHANNEL_ID},
                "feeds": [{"field1": "28.50"}, {"field1": "broken"}],
            },
        ),
    ],
)
def test_bad_upstream(response: httpx.Response, client_for: ClientFactory) -> None:
    with client_for(lambda r: response) as client:
        assert (
            client.get(f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings").status_code
            == HTTPStatus.BAD_GATEWAY
        )


@pytest.mark.parametrize("body", ["not json", "-1", '{"field1":true}'])
def test_latest_rejects_invalid_upstream(client_for: ClientFactory, body: str) -> None:
    with client_for(lambda r: httpx.Response(HTTPStatus.OK, text=body)) as client:
        assert (
            client.get(f"/api/v1/channels/{SENSOR_CHANNEL_ID}/latest").status_code
            == HTTPStatus.BAD_GATEWAY
        )


@pytest.mark.parametrize(
    "limit",
    [None, MIN_HISTORY_LIMIT, MAX_HISTORY_LIMIT],
    ids=["default", "minimum", "maximum"],
)
def test_history_limits_and_full_response(
    client_for: ClientFactory,
    sensor_payload: dict[str, object],
    expected_sensor: Reading,
    limit: int | None,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        expected_limit = DEFAULT_HISTORY_LIMIT if limit is None else limit
        assert dict(request.url.params) == {"results": str(expected_limit)}
        return httpx.Response(
            HTTPStatus.OK,
            json={"channel": {"id": SENSOR_CHANNEL_ID}, "feeds": [sensor_payload]},
        )

    with client_for(handler) as client:
        response = client.get(
            f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings",
            params={} if limit is None else {"limit": limit},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == [expected_sensor]


def test_empty_history(client_for: ClientFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            HTTPStatus.OK, json={"channel": {"id": SENSOR_CHANNEL_ID}, "feeds": []}
        )

    with client_for(handler) as client:
        response = client.get(f"/api/v1/channels/{SENSOR_CHANNEL_ID}/readings")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == []


@pytest.mark.parametrize("endpoint", ["latest", "readings"])
def test_actuator_contract_and_channel_specific_key(
    client_for: ClientFactory, endpoint: str
) -> None:
    payload = {"field1": "0", "field2": "1", "field3": "0"}
    expected = {
        "channel_id": ACTUATOR_CHANNEL_ID,
        "fields": {"field1": 0, "field2": 1, "field3": 0},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["api_key"] == "actuator-key"
        body = (
            payload
            if endpoint == "latest"
            else {"channel": {"id": ACTUATOR_CHANNEL_ID}, "feeds": [payload]}
        )
        return httpx.Response(HTTPStatus.OK, json=body)

    settings = Settings(
        read_keys={SENSOR_CHANNEL_ID: "sensor-key", ACTUATOR_CHANNEL_ID: "actuator-key"}
    )
    with client_for(handler, settings) as client:
        response = client.get(f"/api/v1/channels/{ACTUATOR_CHANNEL_ID}/{endpoint}")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == (expected if endpoint == "latest" else [expected])
        assert "key" not in response.text
