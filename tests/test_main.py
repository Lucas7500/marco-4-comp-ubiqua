from http import HTTPStatus

from conftest import ClientFactory


def test_swagger_and_openapi_do_not_access_network(client_for: ClientFactory) -> None:
    with client_for() as client:
        docs = client.get("/docs")
        assert docs.status_code == HTTPStatus.OK
        assert '"tryItOutEnabled": true' in docs.text
        assert "/openapi.json" in docs.text
        response = client.get("/openapi.json")
        assert response.status_code == HTTPStatus.OK
        paths = response.json()["paths"]
        for path in (
            "/health",
            "/api/v1/channels",
            "/api/v1/channels/{channel_id}/readings",
            "/api/v1/channels/{channel_id}/latest",
        ):
            assert "get" in paths[path]
