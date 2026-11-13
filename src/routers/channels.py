from datetime import UTC, datetime
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from config import CHANNELS
from constants import (
    DEFAULT_HISTORY_LIMIT,
    MAX_FIELD_NUMBER,
    MAX_HISTORY_LIMIT,
    MIN_FIELD_NUMBER,
    MIN_HISTORY_LIMIT,
)
from models.contracts import Channel, Reading
from utils.thingspeak_readings_client import ThingSpeakReadingsClient

router: APIRouter = APIRouter(prefix="/api/v1/channels")


def channel(channel_id: int) -> None:
    if channel_id not in CHANNELS:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Canal não configurado")


@router.get("", response_model=None)
async def channels() -> list[Channel]:
    return [{"channel_id": c, **metadata} for c, metadata in CHANNELS.items()]


@router.get("/{channel_id}/readings", response_model=None)
async def readings(
    request: Request,
    channel_id: int,
    limit: Annotated[
        int, Query(ge=MIN_HISTORY_LIMIT, le=MAX_HISTORY_LIMIT)
    ] = DEFAULT_HISTORY_LIMIT,
    start: datetime | None = None,
    end: datetime | None = None,
    field: Annotated[
        int | None, Query(ge=MIN_FIELD_NUMBER, le=MAX_FIELD_NUMBER)
    ] = None,
) -> list[Reading]:
    channel(channel_id)
    dates: dict[str, datetime] = {}
    for key, value in (("start", start), ("end", end)):
        if value is not None:
            if value.tzinfo is None:
                raise HTTPException(
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    "Informe datas ISO 8601 com fuso horário",
                )
            dates[key] = value.astimezone(UTC)
    if start and end and dates["start"] > dates["end"]:
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY, "start deve ser anterior ou igual a end"
        )
    params: dict[str, str | int] = {
        "results": limit,
        **{k: v.strftime("%Y-%m-%d %H:%M:%S") for k, v in dates.items()},
    }
    client = ThingSpeakReadingsClient(
        request.app.state.http, request.app.state.settings
    )
    return await client.fetch_readings(channel_id, params=params, field=field)


@router.get("/{channel_id}/latest", response_model=None)
async def latest(request: Request, channel_id: int) -> Reading:
    channel(channel_id)
    client = ThingSpeakReadingsClient(
        request.app.state.http, request.app.state.settings
    )
    return await client.fetch_readings(channel_id, latest=True)
