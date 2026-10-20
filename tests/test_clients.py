from __future__ import annotations

import inspect
import json
from pathlib import Path

import httpx
import pytest

from builtwith_official import (
    APIError,
    AsyncBuiltWith,
    AuthenticationError,
    BuiltWith,
    EntitlementError,
    RateLimitError,
    ResponseError,
    TimeoutError,
    TransportError,
)

MANIFEST = json.loads((Path(__file__).parents[1] / "docs/endpoints.json").read_text())


@pytest.mark.parametrize("endpoint", MANIFEST, ids=lambda x: x["method"])
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_all_endpoint_contracts(endpoint, asynchronous):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"future": {"unknown": [1, None]}, "Errors": []})

    cls = AsyncBuiltWith if asynchronous else BuiltWith
    client = cls("test-credential", transport=httpx.MockTransport(handler))
    kwargs = {}
    if endpoint["required_signature"]:
        name = endpoint["required_signature"].split(":")[0]
        kwargs[name] = "example.com" if name == "lookup" else "Shopify"
    if endpoint["method"] == "mcp_registry":
        kwargs["search"] = "payments"
    try:
        result = getattr(client, endpoint["method"])(**kwargs)
        if asynchronous:
            result = await result
        request = requests[0]
        assert request.url.path == endpoint["path"]
        assert "KEY" not in request.url.params
        assert request.headers.get("Authorization") == (
            "API test-credential" if endpoint["authentication"] else None
        )
        assert result.data["future"] == {"unknown": [1, None]}
        assert json.loads(result.content) == result.data
        assert "test-credential" not in repr(client)
        assert "test-credential" not in repr(result)
    finally:
        if asynchronous:
            await client.aclose()
        else:
            client.close()


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "status,body,error",
    [
        (401, {}, AuthenticationError),
        (403, {}, EntitlementError),
        (402, {}, EntitlementError),
        (429, {}, RateLimitError),
        (500, {}, APIError),
        (302, {}, APIError),
        (200, {"Errors": [{"Code": -2}]}, AuthenticationError),
        (200, {"Errors": [{"Code": -3}]}, EntitlementError),
        (200, {"Errors": [{"Code": -5}]}, EntitlementError),
        (200, {"Errors": [{"Code": -8}], "Results": [{"partial": True}]}, APIError),
        (200, {"Errors": ["new error format"]}, APIError),
    ],
)
async def test_errors(status, body, error, asynchronous):
    transport = httpx.MockTransport(lambda r: httpx.Response(status, json=body))
    client = (AsyncBuiltWith if asynchronous else BuiltWith)("secret", transport=transport)
    with pytest.raises(error) as caught:
        if asynchronous:
            await client.usage()
        else:
            client.usage()
    assert caught.value.status_code == status
    assert caught.value.response.data == body
    assert "secret" not in str(caught.value)
    if asynchronous:
        await client.aclose()
    else:
        client.close()


def test_auth_and_public_calls(monkeypatch):
    monkeypatch.delenv("BUILTWITH_API_KEY", raising=False)
    with BuiltWith(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[]))) as client:
        with pytest.raises(AuthenticationError):
            client.usage()
        assert client.vat_types().data == []
    monkeypatch.setenv("BUILTWITH_API_KEY", "environment-key")

    def handler(r):
        assert r.headers["Authorization"] == "API environment-key"
        return httpx.Response(200, json={})

    with BuiltWith(transport=httpx.MockTransport(handler)) as client:
        client.usage()


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("failure", ["status", "timeout", "network"])
async def test_retries(asynchronous, failure, monkeypatch):
    calls = []
    sleeps = []

    def handler(r):
        calls.append(r)
        if len(calls) == 1:
            if failure == "timeout":
                raise httpx.ReadTimeout("contains secret", request=r)
            if failure == "network":
                raise httpx.ConnectError("contains secret", request=r)
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"ok": True})

    async def asleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr("builtwith_official._client.time.sleep", sleeps.append)
    monkeypatch.setattr("builtwith_official._async_client.asyncio.sleep", asleep)
    client = (AsyncBuiltWith if asynchronous else BuiltWith)(
        "secret", max_retries=1, transport=httpx.MockTransport(handler)
    )
    if asynchronous:
        async with client:
            assert (await client.usage()).data == {"ok": True}
    else:
        with client:
            assert client.usage().data == {"ok": True}
    assert len(calls) == 2
    assert sleeps == [2 if failure == "status" else 0.5]
    assert client._http.is_closed


@pytest.mark.parametrize(
    "exception,error", [(httpx.ReadTimeout, TimeoutError), (httpx.ConnectError, TransportError)]
)
async def test_transport_failure_sanitized(exception, error):
    def handler(r):
        raise exception("secret", request=r)

    for cls in (BuiltWith, AsyncBuiltWith):
        client = cls("secret", transport=httpx.MockTransport(handler))
        with pytest.raises(error) as caught:
            if cls is BuiltWith:
                client.usage()
            else:
                await client.usage()
        assert "secret" not in str(caught.value)
        assert caught.value.__context__ is None
        if cls is BuiltWith:
            client.close()
        else:
            await client.aclose()


def test_malformed_and_flat_responses():
    for content in (b"not json", b"null", b"42", b'"text"'):
        with (
            BuiltWith(
                "key",
                transport=httpx.MockTransport(
                    lambda r, content=content: httpx.Response(200, content=content)
                ),
            ) as client,
            pytest.raises(ResponseError),
        ):
            client.usage()
    with BuiltWith(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json=[{"Number": "00123", "future": True}])
        )
    ) as client:
        assert client.vat_types().data[0]["Number"] == "00123"


def test_parameters_and_validation():
    requests = []

    def handler(r):
        requests.append(r)
        return httpx.Response(200, json={})

    with BuiltWith("key", transport=httpx.MockTransport(handler)) as client:
        client.domain(["example.com", "builtwith.com"], no_pii=True, live_only=False)
        assert dict(requests[-1].url.params) == {
            "LOOKUP": "example.com,builtwith.com",
            "NOPII": "yes",
            "LIVEONLY": "no",
        }
        client.ask("shops in Spain", commit=True)
        assert requests[-1].url.params["COMMIT"] == "true"
        client.changes("example.com", since="last month")
        assert requests[-1].url.params["SINCE"] == "last month"
        for invalid in ([], ["x"] * 17, "", "a,,b"):
            with pytest.raises(ValueError):
                client.domain(invalid)
        with pytest.raises(ValueError):
            client.relationships("a,b")
        with pytest.raises(ValueError):
            client.lists("Shopify", since="yesterday", all_sites=True)
        with pytest.raises(ValueError):
            client.vector_search("x", limit=101)
        with pytest.raises(ValueError):
            client.keyword_search("x", limit=15)
        with pytest.raises(ValueError):
            client.mcp_registry()
        with pytest.raises(ValueError):
            client.relationships("example.com", page=0)
        with pytest.raises(ValueError):
            client.bulk_status("../usage")


def test_matching_signatures():
    for name, method in inspect.getmembers(BuiltWith, inspect.isfunction):
        if not name.startswith("_") and name != "close":
            assert inspect.signature(method) == inspect.signature(
                getattr(AsyncBuiltWith, name)
            ) or name.endswith("_pages")


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_bulk_never_retried(asynchronous):
    calls = []

    def handler(r):
        calls.append(r)
        return httpx.Response(503, json={})

    client = (AsyncBuiltWith if asynchronous else BuiltWith)(
        "key", max_retries=3, transport=httpx.MockTransport(handler)
    )
    for name, value in [
        ("bulk_submit", ["example.com"]),
        ("bulk_result", "00000000-0000-0000-0000-000000000001"),
    ]:
        with pytest.raises(APIError):
            result = getattr(client, name)(value)
            if asynchronous:
                await result
    assert len(calls) == 2
    assert calls[0].method == "POST"
    assert json.loads(calls[0].content)["options"]["noPii"] is True
    if asynchronous:
        await client.aclose()
    else:
        client.close()


def test_bulk_accepted_and_timeout_configuration():
    def handler(r):
        assert r.extensions["timeout"]["read"] == 7
        return httpx.Response(202, json={"job_id": "job", "status": "queued"})

    with BuiltWith("key", timeout=7, transport=httpx.MockTransport(handler)) as client:
        assert client.bulk_submit(["example.com"]).status_code == 202
