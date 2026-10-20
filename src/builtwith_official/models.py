"""Lossless JSON types: optional and future API fields are preserved."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

JSONValue: TypeAlias = "None | bool | int | float | str | list[JSONValue] | dict[str, JSONValue]"
Params: TypeAlias = dict[str, str | int | bool | None]


@dataclass(frozen=True)
class APIResponse:
    """Decoded JSON, original response bytes, status and lowercase response headers.

    No HTTP request object is retained, so repr never contains request credentials.
    Treat API data as potentially sensitive customer information.
    """

    data: JSONValue
    status_code: int
    headers: dict[str, str]
    content: bytes
