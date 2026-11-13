"""Shared types for channel metadata and normalized readings."""

from typing import Literal, NotRequired, TypedDict

type FieldValue = int | float | str | None


class Reading(TypedDict):
    channel_id: int
    fields: dict[str, FieldValue]
    entry_id: NotRequired[int]
    created_at: NotRequired[str]


class FieldMetadata(TypedDict):
    name: str
    type: Literal["float", "integer"]
    unit: NotRequired[str]
    states: NotRequired[dict[int, str]]


class ChannelMetadata(TypedDict):
    name: str
    fields: dict[str, FieldMetadata]


class Channel(ChannelMetadata):
    channel_id: int
