"""Shared response, validation and pagination logic."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import cast
from urllib.parse import parse_qs, urlsplit

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    EntitlementError,
    RateLimitError,
    ResponseError,
)
from .models import APIResponse, JSONValue, Params

BASE_URL = "https://api.builtwith.com"
RETRY_STATUSES = {429, 500, 502, 503, 504}


def validate_config(retries: int, backoff: float, max_retry_after: float) -> None:
    if isinstance(retries, bool) or not isinstance(retries, int) or not 0 <= retries <= 10:
        raise ValueError("max_retries must be an integer between 0 and 10")
    if not math.isfinite(backoff) or backoff < 0:
        raise ValueError("backoff_factor must be finite and nonnegative")
    if not math.isfinite(max_retry_after) or max_retry_after < 0:
        raise ValueError("max_retry_after must be finite and nonnegative")


def parameters(values: Params) -> dict[str, str | int]:
    result: dict[str, str | int] = {}
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{key} must not be empty")
        if isinstance(value, bool):
            result[key] = (
                ("true" if value else "false") if key == "COMMIT" else ("yes" if value else "no")
            )
        else:
            result[key] = value
    for key in ("PAGE", "LIMIT", "OFFSET"):
        value = values.get(key)
        if isinstance(value, int) and (
            isinstance(value, bool) or value < (1 if key == "PAGE" else 0)
        ):
            raise ValueError(f"{key} is outside its supported range")
    return result


def lookup(value: str | list[str], maximum: int = 16) -> str:
    parts = value.split(",") if isinstance(value, str) else value
    if not 1 <= len(parts) <= maximum or any(not p.strip() for p in parts):
        raise ValueError(f"LOOKUP requires 1 to {maximum} nonempty domains")
    return ",".join(p.strip() for p in parts)


def delay(response: httpx.Response | None, attempt: int, factor: float) -> float:
    if response is not None:
        value = response.headers.get("retry-after", "")
        try:
            seconds = float(value)
            if math.isfinite(seconds):
                return max(0.0, seconds)
        except ValueError:
            try:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                return max(0.0, (date - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return min(60.0, factor * float(2**attempt))


def parse(response: httpx.Response) -> APIResponse:
    try:
        data = cast(JSONValue, response.json())
    except (ValueError, UnicodeError):
        data = None
    result = APIResponse(data, response.status_code, dict(response.headers), response.content)
    errors = data.get("Errors") if isinstance(data, dict) else None
    codes = tuple(
        cast(int, item["Code"])
        for item in (errors if isinstance(errors, list) else [])
        if isinstance(item, dict) and isinstance(item.get("Code"), int)
    )
    error_type: type[APIError] | None = None
    if response.status_code == 401 or -2 in codes:
        error_type = AuthenticationError
    elif response.status_code == 429:
        error_type = RateLimitError
    elif response.status_code in (402, 403) or any(c in (-3, -5) for c in codes):
        error_type = EntitlementError
    elif not 200 <= response.status_code < 300 or errors:
        error_type = APIError
    if error_type:
        raise error_type("BuiltWith API request failed", response=result, codes=codes)
    if not isinstance(data, (dict, list)):
        raise ResponseError("Expected a JSON object or array", response=result)
    return result


def next_params(kind: str, response: APIResponse, current: Params) -> Params | None:
    """Read only documented cursor fields; never follow server-supplied URLs."""
    data = response.data
    updated = current.copy()
    if kind == "registry":
        if response.headers.get("x-has-more", "").lower() not in ("true", "1"):
            return None
        try:
            offset = int(response.headers["x-offset"])
            size = int(response.headers["x-page-size"])
            if size <= 0 or offset < 0:
                raise ValueError
            updated["OFFSET"] = offset + size
        except (KeyError, ValueError):
            raise ResponseError("Invalid registry pagination headers", response=response) from None
    elif isinstance(data, dict):
        if kind == "relationships":
            if not data.get("more_results"):
                return None
            page = data.get("next_page")
            if not isinstance(page, int) or isinstance(page, bool) or page <= 0:
                raise ResponseError("Invalid next_page", response=response)
            updated["PAGE"] = page
        elif kind == "product":
            if not data.get("is_more"):
                return None
            url = data.get("next_page")
            if not isinstance(url, str):
                raise ResponseError("Missing product next_page", response=response)
            query = parse_qs(urlsplit(url).query)
            try:
                page_number = int(query["PAGE"][0])
                if page_number < 1:
                    raise ValueError
                updated["PAGE"] = page_number
                if "LIMIT" in query:
                    updated["LIMIT"] = int(query["LIMIT"][0])
            except (KeyError, ValueError):
                raise ResponseError("Invalid product next_page", response=response) from None
        else:
            cursor = data.get("NextOffset")
            if cursor in (None, "", "END"):
                return None
            if not isinstance(cursor, str):
                raise ResponseError("Invalid NextOffset", response=response)
            updated["NEXTOFFSET" if kind == "ask" else "OFFSET"] = cursor
    else:
        raise ResponseError("Expected pagination object", response=response)
    if updated == current:
        raise ResponseError("Pagination cursor did not advance", response=response)
    return updated


def fingerprint(params: Params) -> str:
    return json.dumps(params, sort_keys=True)
