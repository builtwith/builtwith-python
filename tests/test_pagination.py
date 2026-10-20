import httpx
import pytest

from builtwith_official import AsyncBuiltWith, BuiltWith, ResponseError


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "method,args,first,last,wire,expected,headers",
    [
        (
            "lists_pages",
            ["Shopify"],
            {"NextOffset": "opaque"},
            {"NextOffset": "END"},
            "OFFSET",
            "opaque",
            {},
        ),
        (
            "ask_pages",
            ["shops"],
            {"NextOffset": "opaque"},
            {"NextOffset": "END"},
            "NEXTOFFSET",
            "opaque",
            {},
        ),
        ("keyword_search_pages", ["perfume"], {"NextOffset": "abc"}, {}, "OFFSET", "abc", {}),
        (
            "relationships_pages",
            ["example.com"],
            {"more_results": True, "next_page": 2},
            {"more_results": False},
            "PAGE",
            "2",
            {},
        ),
        (
            "product_search_pages",
            ["shoes"],
            {
                "is_more": True,
                "next_page": "https://evil.example/steal?KEY=bad&QUERY=wrong&PAGE=1&LIMIT=50",
            },
            {"is_more": False},
            "PAGE",
            "1",
            {},
        ),
        (
            "mcp_registry_pages",
            [],
            [],
            [],
            "OFFSET",
            "100",
            {"X-HAS-MORE": "true", "X-OFFSET": "0", "X-PAGE-SIZE": "100"},
        ),
    ],
)
async def test_pagination(asynchronous, method, args, first, last, wire, expected, headers):
    requests = []

    def handler(r):
        requests.append(r)
        assert r.url.host == "api.builtwith.com"
        assert "KEY" not in r.url.params
        if len(requests) == 1:
            return httpx.Response(200, json=first, headers=headers)
        assert r.url.params[wire] == expected
        if method == "product_search_pages":
            assert r.url.params["QUERY"] == "shoes"
        return httpx.Response(200, json=last)

    client = (AsyncBuiltWith if asynchronous else BuiltWith)(
        "key", transport=httpx.MockTransport(handler)
    )
    kwargs = {"search": "payments"} if method == "mcp_registry_pages" else {}
    iterator = getattr(client, method)(*args, **kwargs)
    if asynchronous:
        async with client:
            pages = [page async for page in iterator]
    else:
        with client:
            pages = list(iterator)
    assert len(pages) == 2


def test_cycles_bounds_and_missing_fields():
    with BuiltWith(
        "key",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"NextOffset": "same"})),
    ) as client:
        assert len(list(client.lists_pages("Shopify", max_pages=1))) == 1
        with pytest.raises(ResponseError):
            list(client.lists_pages("Shopify"))
        with pytest.raises(ValueError):
            list(client.lists_pages("Shopify", max_pages=0))
    with BuiltWith(
        "key", transport=httpx.MockTransport(lambda r: httpx.Response(200, json={}))
    ) as client:
        assert len(list(client.lists_pages("Shopify"))) == 1


@pytest.mark.parametrize(
    "method,body,headers",
    [
        ("relationships_pages", {"more_results": True}, {}),
        ("product_search_pages", {"is_more": True}, {}),
        ("mcp_registry_pages", [], {"X-HAS-MORE": "true"}),
        ("lists_pages", {"NextOffset": ["bad"]}, {}),
    ],
)
def test_invalid_pagination(method, body, headers):
    with (
        BuiltWith(
            "key",
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, json=body, headers=headers)
            ),
        ) as client,
        pytest.raises(ResponseError),
    ):
        if method == "mcp_registry_pages":
            list(client.mcp_registry_pages(search="payments"))
        else:
            list(getattr(client, method)("example.com"))
