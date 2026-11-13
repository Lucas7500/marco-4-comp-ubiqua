from collections.abc import Mapping
from http import HTTPStatus
from typing import Literal, overload

import httpx
from fastapi import HTTPException

from config import Settings
from models.contracts import Reading
from utils.reading_normalizer import ReadingNormalizer

type QueryParams = Mapping[str, str | int | float | bool | None]


class ThingSpeakReadingsClient:
    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self.client: httpx.AsyncClient = client
        self.settings: Settings = settings

    @overload
    async def fetch_readings(
        self,
        channel_id: int,
        *,
        latest: Literal[True],
        params: QueryParams | None = None,
        field: int | None = None,
    ) -> Reading: ...

    @overload
    async def fetch_readings(
        self,
        channel_id: int,
        *,
        latest: Literal[False] = False,
        params: QueryParams | None = None,
        field: int | None = None,
    ) -> list[Reading]: ...

    async def fetch_readings(
        self,
        channel_id: int,
        *,
        latest: bool = False,
        params: QueryParams | None = None,
        field: int | None = None,
    ) -> Reading | list[Reading]:
        query = dict(params or {})
        if key := self.settings.read_keys.get(channel_id):
            query["api_key"] = key
        try:
            if latest:
                return await self._fetch_latest(channel_id, query)
            return await self._fetch_history(channel_id, query, field)
        except httpx.TimeoutException:
            raise HTTPException(
                HTTPStatus.GATEWAY_TIMEOUT, "Timeout do ThingSpeak"
            ) from None
        except httpx.RequestError:
            raise HTTPException(
                HTTPStatus.SERVICE_UNAVAILABLE, "ThingSpeak indisponível"
            ) from None
        except (httpx.HTTPStatusError, ValueError, TypeError, OverflowError):
            raise HTTPException(
                HTTPStatus.BAD_GATEWAY,
                "Resposta inválida ou acesso negado pelo ThingSpeak",
            ) from None

    async def _fetch_data(
        self, channel_id: int, path: str, query: QueryParams
    ) -> object:
        response = await self.client.get(
            f"https://api.thingspeak.com/channels/{channel_id}/{path}", params=query
        )
        response.raise_for_status()
        return response.json()

    async def _fetch_latest(self, channel_id: int, query: QueryParams) -> Reading:
        data = await self._fetch_data(channel_id, "feeds/last.json", query)
        if data is None or data == {}:
            raise HTTPException(HTTPStatus.NOT_FOUND, "Canal sem medições")
        return ReadingNormalizer(channel_id).normalize(data)

    async def _fetch_history(
        self, channel_id: int, query: QueryParams, field: int | None
    ) -> list[Reading]:
        data = await self._fetch_data(channel_id, "feeds.json", query)
        if not isinstance(data, dict) or not isinstance(data.get("feeds"), list):
            raise ValueError("Histórico inválido")  # noqa: TRY004 - Preserve the validation exception contract.
        if (
            not isinstance(data.get("channel"), dict)
            or data["channel"].get("id") != channel_id
        ):
            raise ValueError("Canal inesperado")
        normalizer = ReadingNormalizer(channel_id)
        readings = [normalizer.normalize(item) for item in data["feeds"]]
        if field:
            for item in readings:
                item["fields"] = {
                    k: v for k, v in item["fields"].items() if k == f"field{field}"
                }
        return readings
