"""Shared data and isolated application clients; no real credentials or network."""

from collections.abc import Callable, Iterator
from typing import NoReturn, Protocol

import httpx
import pytest
from fastapi.testclient import TestClient

from config import Settings
from constants import SENSOR_CHANNEL_ID
from main import create_app
from models.contracts import Reading

type RequestHandler = Callable[[httpx.Request], httpx.Response]


class ClientFactory(Protocol):
    def __call__(
        self,
        handler: RequestHandler | None = None,
        settings: Settings | None = None,
    ) -> TestClient: ...


@pytest.fixture
def sensor_payload() -> dict[str, object]:
    return {
        "field1": "28.50",
        "field2": None,
        "field3": "2000.00",
        "entry_id": 7,
        "created_at": "2026-01-01T10:00:00Z",
    }


@pytest.fixture
def expected_sensor() -> Reading:
    return {
        "channel_id": SENSOR_CHANNEL_ID,
        "fields": {"field1": 28.5, "field2": None, "field3": 2000.0},
        "entry_id": 7,
        "created_at": "2026-01-01T10:00:00Z",
    }


@pytest.fixture
def client_for() -> ClientFactory:
    def reject_request(request: httpx.Request) -> NoReturn:
        pytest.fail(f"Unexpected HTTP request: {request.method} {request.url.path}")

    def make_client(
        handler: RequestHandler | None = None, settings: Settings | None = None
    ) -> TestClient:
        app = create_app(
            settings if settings is not None else Settings(),
            httpx.MockTransport(handler or reject_request),
        )
        return TestClient(app)

    return make_client


@pytest.fixture
def client(client_for: ClientFactory) -> Iterator[TestClient]:
    with client_for() as client:
        yield client
