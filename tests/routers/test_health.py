from http import HTTPStatus

from fastapi.testclient import TestClient


def test_health_does_not_access_network(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}
