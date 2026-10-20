import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest

from builtwith_official import AsyncBuiltWith, BuiltWith, RateLimitError
from builtwith_official._core import delay


def test_retry_after_dates_and_fallback():
    future = datetime.now(timezone.utc) + timedelta(seconds=30)
    response = httpx.Response(429, headers={"Retry-After": format_datetime(future)})
    assert 28 <= delay(response, 0, 0.5) <= 30
    for invalid in ("invalid", "NaN", "Infinity"):
        assert delay(httpx.Response(429, headers={"Retry-After": invalid}), 2, 0.5) == 2
    assert delay(httpx.Response(429, headers={"Retry-After": "-2"}), 0, 0.5) == 0
    assert delay(None, 10, 1) == 60


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_retry_after_too_long_is_not_retried(asynchronous):
    requests = []

    def handler(r):
        requests.append(r)
        return httpx.Response(429, headers={"Retry-After": "3600"}, json={})

    client = (AsyncBuiltWith if asynchronous else BuiltWith)(
        "key", max_retries=3, transport=httpx.MockTransport(handler)
    )
    with pytest.raises(RateLimitError):
        if asynchronous:
            async with client:
                await client.usage()
        else:
            with client:
                client.usage()
    assert len(requests) == 1


async def test_cancellation_propagates_and_closes():
    async def handler(r):
        raise asyncio.CancelledError

    client = AsyncBuiltWith("key", max_retries=3, transport=httpx.MockTransport(handler))
    with pytest.raises(asyncio.CancelledError):
        async with client:
            await client.usage()
    assert client._http.is_closed


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_retries": -1},
        {"max_retries": True},
        {"max_retries": 11},
        {"backoff_factor": -1},
        {"backoff_factor": float("nan")},
        {"max_retry_after": float("inf")},
        {"api_key": "a\r\nb"},
    ],
)
def test_invalid_configuration(kwargs):
    for cls in (BuiltWith, AsyncBuiltWith):
        with pytest.raises(ValueError):
            cls(**kwargs)


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_retry_exhaustion(asynchronous, monkeypatch):
    requests = []
    waits = []

    def handler(r):
        requests.append(r)
        return httpx.Response(429, json={})

    async def asleep(seconds):
        waits.append(seconds)

    monkeypatch.setattr("builtwith_official._client.time.sleep", waits.append)
    monkeypatch.setattr("builtwith_official._async_client.asyncio.sleep", asleep)
    client = (AsyncBuiltWith if asynchronous else BuiltWith)(
        "key", max_retries=2, transport=httpx.MockTransport(handler)
    )
    with pytest.raises(RateLimitError):
        if asynchronous:
            async with client:
                await client.usage()
        else:
            with client:
                client.usage()
    assert len(requests) == 3
    assert waits == [0.5, 1.0]
