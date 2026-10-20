# BuiltWith Python SDK

Official Python client for BuiltWith technology, company, and website intelligence.
Python 3.10+, synchronous and asynchronous HTTPX clients, typed interfaces, and optional MCP tools.

## Install

```bash
python -m pip install builtwith-official
# Optional integration with the existing BuiltWith MCP server:
python -m pip install "builtwith-official[mcp]"
```

Import from `builtwith_official`, not `builtwith`: the latter is an unrelated existing
PyPI distribution. For development, install from this checkout with `pip install -e ".[dev,mcp]"`.

## First request

No API key or credits are needed for public VAT registration types:

```python
from builtwith_official import BuiltWith

with BuiltWith() as client:
    print(client.vat_types().data)
```

Get an API key from [BuiltWith API](https://api.builtwith.com).
Set `BUILTWITH_API_KEY` in your environment or secret manager:

```bash
export BUILTWITH_API_KEY="YOUR_API_KEY"
```

PowerShell: `$env:BUILTWITH_API_KEY = "YOUR_API_KEY"`.

```python
from builtwith_official import BuiltWith

with BuiltWith() as client:
    print(client.usage().data)  # No credits used
    result = client.domain("shopify.com", no_pii=True)  # Uses API credits
    print(result.data)
    print(result.headers.get("x-api-credits-remaining"))
```

An explicit `BuiltWith(api_key="YOUR_API_KEY")` overrides the environment. Empty keys
disable authenticated calls but still allow public reference requests. Credentials are
sent in `Authorization: API …`, never a query parameter. The SDK does not log requests,
credentials or response bodies. Avoid logging raw customer data or enabling third-party
HTTP tracing that records authorization headers. Proxy environment variables are ignored;
configure a transport explicitly when needed.

## Async and notebooks

```python
import asyncio
from builtwith_official import AsyncBuiltWith


async def main() -> None:
    async with AsyncBuiltWith() as client:
        result = await client.domain("shopify.com", no_pii=True)
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
```

In Jupyter use `await main()` instead of `asyncio.run`. Reuse one async client per
application lifespan in FastAPI; close it with `await client.aclose()`. See
[examples](https://github.com/builtwith/builtwith-python/tree/main/examples/) for FastAPI, pipelines, agent functions and optional framework adapters.
The core installation does not depend on any AI framework.

## Responses and errors

Every API method returns `APIResponse(data, status_code, headers, content)`.
`data` is recursively typed JSON (`JSONValue`), preserving original spelling, unknown
fields, arrays, missing fields, and registration numbers with leading zeros. No model
silently drops new fields. Narrow dictionaries/lists before accessing nested values.
`content` contains original response bytes; headers use lowercase keys. No authenticated
request object is attached.

```python
from builtwith_official import BuiltWith, APIError, RateLimitError, TimeoutError

with BuiltWith(timeout=15, max_retries=2) as client:
    try:
        result = client.trends("Shopify")
    except RateLimitError as error:
        print("Rate limited", error.status_code)
    except TimeoutError:
        print("Request timed out")
    except APIError as error:
        print("API failure", error.status_code, error.codes)
        # error.response retains the payload, including any partial successes.
```

`AuthenticationError` covers missing keys, HTTP 401 and documented API error -2.
`EntitlementError` covers HTTP 402/403 and codes -3/-5. Other application `Errors`,
including errors in HTTP 200 responses, raise `APIError`. Malformed success responses
raise `ResponseError`; connection failures raise `TransportError`. Exception messages
omit upstream text and URLs; explicitly inspected response data may contain sensitive values.

## Retries, limits and pagination

Defaults: 30-second HTTPX timeout per operation, no retries. `max_retries=2` enables
exponential backoff (0.5 seconds initially, at most 60 seconds) for transport failures,
timeouts, and HTTP 429/500/502/503/504. `Retry-After` seconds and HTTP dates take precedence.
A server delay above `max_retry_after` (default 120 seconds) stops retries instead of
retrying early. Retries may incur additional credits; no automatic retries apply to
bulk submission or one-time bulk results. There is no global request-rate scheduler.
Coordinate callers with account limits from `whoami()`: documentation gives 10 requests
per second / 8 concurrent requests generally, and 1 request per second for the MCP registry.

```python
with BuiltWith() as client:
    for page in client.lists_pages("Shopify", country="US", max_pages=5):
        print(page.data)
```

Async: `async for page in client.lists_pages(...)`.
Page iterators are lazy, preserve filters, yield complete `APIResponse` objects, stop
at the documented end marker, reject repeated cursors, and stop at `max_pages` (100 by
default). That bound intentionally truncates iteration; use the last response cursor to
resume if needed. No requests occur until iteration. Helpers cover Lists, Ask, Keyword
Search, Relationships, Product Search and MCP Registry. Product URLs are parsed only for
page parameters; the SDK never follows their host or embedded credentials.

## Coverage and access

See the [complete method signatures](https://github.com/builtwith/builtwith-python/blob/main/docs/api-reference.md) and
[machine-readable endpoint inventory](https://github.com/builtwith/builtwith-python/blob/main/docs/endpoints.json).

| Capability | API version / access |
| --- | --- |
| Domain, changes, relationships | v26, change1, rv5; credits |
| Free summary, trends, account identity and usage | free1, trends/v6, whoamiv1, usagev2; key, no credits |
| Lists and keyword search | lists13, kws1; subscription required |
| Ask, company-to-URL, tags, recommendations, redirects, keywords | ask1, ctu3, tag1, rec1, redirect1, kw2; credits |
| Product, trust, vector search | productv1, trustv2, vector/v1; credits |
| VAT | vat1; 1 credit per domain returning records, 1–16 domains |
| VAT types and MCP categories | Public; no key or credits |
| MCP registry | mcp2; key, no credits; 1 request/second |
| Bulk domain | v23/domain/bulk; credits per domain |

Domain `trust=True` adds an extra Trust API credit. Ask normally returns a sample;
`commit=True` runs a full report. Lists/prospect access requires a plan; lookup credits
alone do not grant it. Confirm current entitlements, costs and batch limits through
`whoami()` before large workloads. Relationships may reuse one domain credit across
pages while its server cache survives; cache eviction or server changes can charge again.
Change API credit details are not specified in the local reference; inspect account
costs rather than assume a free call.

Bulk jobs accept up to the account limit (documented ceiling 5000).
`bulk_submit()` may return synchronous results or HTTP 202 with a job ID.
Poll `bulk_status(job_id)` at an application-controlled interval.
`bulk_result(job_id)` is consumed/deleted after successful retrieval: persist its response.
The SDK does not auto-poll or auto-retrieve jobs.

## MCP and agents

[MCP setup](https://github.com/builtwith/builtwith-python/blob/main/docs/mcp.md) covers Python client integration with the existing hosted
BuiltWith endpoint. [Agent guidance](https://github.com/builtwith/builtwith-python/blob/main/docs/agents.md) provides function schemas and
framework integration advice. [llms.txt](https://github.com/builtwith/builtwith-python/blob/main/docs/llms.txt) is a proposal for future public
documentation; this change does not modify the BuiltWith website.

## Development and distribution

See [development and release instructions](https://github.com/builtwith/builtwith-python/blob/main/docs/development.md) and [changelog](https://github.com/builtwith/builtwith-python/blob/main/CHANGELOG.md).
MIT license, consistent with the existing BuiltWith MCP and examples repositories.

The implementation follows the workspace API `llms-full.txt` reference (snapshot inspected
2026-10-20), rather than older endpoint versions in existing clients.
Public reference: [BuiltWith full API documentation](https://api.builtwith.com/llms-full.txt).
Known scope exclusions and discovery findings are in [discovery.md](https://github.com/builtwith/builtwith-python/blob/main/docs/discovery.md).

