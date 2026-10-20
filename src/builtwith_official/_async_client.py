"""Asynchronous BuiltWith REST client."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from types import TracebackType
from uuid import UUID

import httpx

from ._core import (
    BASE_URL,
    RETRY_STATUSES,
    delay,
    fingerprint,
    next_params,
    parameters,
    parse,
    validate_config,
)
from ._core import lookup as validate_lookup
from .exceptions import AuthenticationError, ResponseError, TimeoutError, TransportError
from .models import APIResponse, JSONValue, Params


class AsyncBuiltWith:
    """Reusable HTTPX client. Owns and closes its transport; never follows redirects.

    API key defaults to BUILTWITH_API_KEY. Public reference calls need no key.
    Retries default to zero because reissuing a lookup may spend more credits.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float | httpx.Timeout = 30.0,
        max_retries: int = 0,
        backoff_factor: float = 0.5,
        max_retry_after: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        validate_config(max_retries, backoff_factor, max_retry_after)
        self._key = api_key if api_key is not None else os.environ.get("BUILTWITH_API_KEY", "")
        if any(c in self._key for c in ("\r", "\n")):
            raise ValueError("Invalid API key")
        self._retries = max_retries
        self._backoff = backoff_factor
        self._max_retry_after = max_retry_after
        self._http = httpx.AsyncClient(
            timeout=timeout,
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "builtwith-official-python/0.1.1", "Accept": "application/json"},
        )

    async def aclose(self) -> None:
        """Close pooled connections and the supplied transport."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncBuiltWith:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def _request(
        self,
        path: str,
        params: Params | None = None,
        *,
        public: bool = False,
        body: JSONValue = None,
        retry: bool = True,
    ) -> APIResponse:
        if not public and not self._key.strip():
            raise AuthenticationError("Set BUILTWITH_API_KEY or pass api_key")
        headers = {} if public else {"Authorization": "API " + self._key}
        query = parameters(params or {})
        attempts = self._retries if retry else 0
        for attempt in range(attempts + 1):
            response = None
            failure: TransportError | None = None
            try:
                response = await self._http.request(
                    "POST" if body is not None else "GET",
                    BASE_URL + path,
                    params=query,
                    headers=headers,
                    json=body,
                )
            except httpx.TimeoutException:
                failure = TimeoutError("BuiltWith request timed out")
            except httpx.TransportError:
                failure = TransportError("BuiltWith transport failed")
            if failure is not None:
                if attempt == attempts:
                    raise failure from None
            elif response is not None:
                if response.status_code not in RETRY_STATUSES or attempt == attempts:
                    return parse(response)
            wait = delay(response, attempt, self._backoff)
            if wait > self._max_retry_after:
                if response is not None:
                    return parse(response)
                raise TransportError("Retry delay exceeds configured maximum")
            await asyncio.sleep(wait)
        raise AssertionError("unreachable")

    async def _pages(
        self, path: str, params: Params, kind: str, max_pages: int
    ) -> AsyncIterator[APIResponse]:
        if isinstance(max_pages, bool) or not isinstance(max_pages, int) or max_pages < 1:
            raise ValueError("max_pages must be a positive integer")
        seen: set[str] = set()
        for _ in range(max_pages):
            token = fingerprint(params)
            if token in seen:
                raise ResponseError("Pagination cursor repeated")
            seen.add(token)
            response = await self._request(path, params)
            yield response
            following = next_params(kind, response, params)
            if following is None:
                return
            params = following

    async def domain(
        self,
        lookup: str | list[str],
        *,
        hide_text: bool | None = None,
        hide_dl: bool | None = None,
        live_only: bool | None = None,
        no_meta: bool | None = None,
        no_pii: bool | None = None,
        no_attr: bool | None = None,
        ip: bool | None = None,
        trust: bool | None = None,
        first_detected: str | None = None,
        last_detected: str | None = None,
    ) -> APIResponse:
        """Request /v26/api.json. See docs/api-reference.md."""
        params: Params = {
            "LOOKUP": validate_lookup(lookup),
            "HIDETEXT": hide_text,
            "HIDEDL": hide_dl,
            "LIVEONLY": live_only,
            "NOMETA": no_meta,
            "NOPII": no_pii,
            "NOATTR": no_attr,
            "IP": ip,
            "TRUST": trust,
            "FDRANGE": first_detected,
            "LDRANGE": last_detected,
        }
        return await self._request("/v26/api.json", params, public=False)

    async def changes(self, lookup: str | list[str], *, since: str | None = None) -> APIResponse:
        """Request /change1/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": validate_lookup(lookup), "SINCE": since}
        return await self._request("/change1/api.json", params, public=False)

    async def relationships(
        self, lookup: str, *, page: int | None = None, ip: bool | None = None
    ) -> APIResponse:
        """Request /rv5/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": validate_lookup(lookup, 1), "PAGE": page, "IP": ip}
        return await self._request("/rv5/api.json", params, public=False)

    async def relationships_pages(
        self, lookup: str, *, page: int | None = None, ip: bool | None = None, max_pages: int = 100
    ) -> AsyncIterator[APIResponse]:
        """Iterate response pages from /rv5/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": validate_lookup(lookup, 1), "PAGE": page, "IP": ip}
        async for response in self._pages("/rv5/api.json", params, "relationships", max_pages):
            yield response

    async def lists(
        self,
        tech: str,
        *,
        offset: str | None = None,
        country: str | None = None,
        since: str | None = None,
        all_sites: bool | None = None,
        meta: bool | None = None,
        other_techs: str | None = None,
        spend: str | None = None,
        revenue: str | None = None,
        sku: str | None = None,
        followers: str | None = None,
        employees: str | None = None,
        sitemap: str | None = None,
        pagerank: str | None = None,
        bwrank: str | None = None,
        tranco: str | None = None,
        majestic: str | None = None,
        bws: str | None = None,
        ecat: str | None = None,
        aim: str | None = None,
        aio: str | None = None,
        air: str | None = None,
        aiv: str | None = None,
    ) -> APIResponse:
        """Request /lists13/api.json. See docs/api-reference.md."""
        if all_sites and since is not None:
            raise ValueError("all_sites and since cannot be combined")
        params: Params = {
            "TECH": tech,
            "OFFSET": offset,
            "COUNTRY": country,
            "SINCE": since,
            "ALL": all_sites,
            "META": meta,
            "OTHERTECHS": other_techs,
            "SPEND": spend,
            "REVENUE": revenue,
            "SKU": sku,
            "FOLLOWERS": followers,
            "EMPLOYEES": employees,
            "SITEMAP": sitemap,
            "PAGERANK": pagerank,
            "BWRANK": bwrank,
            "TRANCO": tranco,
            "MAJESTIC": majestic,
            "BWS": bws,
            "ECAT": ecat,
            "AIM": aim,
            "AIO": aio,
            "AIR": air,
            "AIV": aiv,
        }
        return await self._request("/lists13/api.json", params, public=False)

    async def lists_pages(
        self,
        tech: str,
        *,
        offset: str | None = None,
        country: str | None = None,
        since: str | None = None,
        all_sites: bool | None = None,
        meta: bool | None = None,
        other_techs: str | None = None,
        spend: str | None = None,
        revenue: str | None = None,
        sku: str | None = None,
        followers: str | None = None,
        employees: str | None = None,
        sitemap: str | None = None,
        pagerank: str | None = None,
        bwrank: str | None = None,
        tranco: str | None = None,
        majestic: str | None = None,
        bws: str | None = None,
        ecat: str | None = None,
        aim: str | None = None,
        aio: str | None = None,
        air: str | None = None,
        aiv: str | None = None,
        max_pages: int = 100,
    ) -> AsyncIterator[APIResponse]:
        """Iterate response pages from /lists13/api.json. See docs/api-reference.md."""
        if all_sites and since is not None:
            raise ValueError("all_sites and since cannot be combined")
        params: Params = {
            "TECH": tech,
            "OFFSET": offset,
            "COUNTRY": country,
            "SINCE": since,
            "ALL": all_sites,
            "META": meta,
            "OTHERTECHS": other_techs,
            "SPEND": spend,
            "REVENUE": revenue,
            "SKU": sku,
            "FOLLOWERS": followers,
            "EMPLOYEES": employees,
            "SITEMAP": sitemap,
            "PAGERANK": pagerank,
            "BWRANK": bwrank,
            "TRANCO": tranco,
            "MAJESTIC": majestic,
            "BWS": bws,
            "ECAT": ecat,
            "AIM": aim,
            "AIO": aio,
            "AIR": air,
            "AIV": aiv,
        }
        async for response in self._pages("/lists13/api.json", params, "lists", max_pages):
            yield response

    async def ask(
        self,
        query: str,
        *,
        commit: bool | None = None,
        next_offset: str | None = None,
        meta: bool | None = None,
    ) -> APIResponse:
        """Request /ask1/api.json. See docs/api-reference.md."""
        params: Params = {"QUERY": query, "COMMIT": commit, "NEXTOFFSET": next_offset, "META": meta}
        return await self._request("/ask1/api.json", params, public=False)

    async def ask_pages(
        self,
        query: str,
        *,
        commit: bool | None = None,
        next_offset: str | None = None,
        meta: bool | None = None,
        max_pages: int = 100,
    ) -> AsyncIterator[APIResponse]:
        """Iterate response pages from /ask1/api.json. See docs/api-reference.md."""
        params: Params = {"QUERY": query, "COMMIT": commit, "NEXTOFFSET": next_offset, "META": meta}
        async for response in self._pages("/ask1/api.json", params, "ask", max_pages):
            yield response

    async def keyword_search(
        self, keyword: str, *, limit: int | None = None, offset: str | None = None
    ) -> APIResponse:
        """Request /kws1/api.json. See docs/api-reference.md."""
        if limit is not None and (isinstance(limit, bool) or not 16 <= limit <= 1000):
            raise ValueError("limit must be between 16 and 1000")
        params: Params = {"KEYWORD": keyword, "LIMIT": limit, "OFFSET": offset}
        return await self._request("/kws1/api.json", params, public=False)

    async def keyword_search_pages(
        self,
        keyword: str,
        *,
        limit: int | None = None,
        offset: str | None = None,
        max_pages: int = 100,
    ) -> AsyncIterator[APIResponse]:
        """Iterate response pages from /kws1/api.json. See docs/api-reference.md."""
        if limit is not None and (isinstance(limit, bool) or not 16 <= limit <= 1000):
            raise ValueError("limit must be between 16 and 1000")
        params: Params = {"KEYWORD": keyword, "LIMIT": limit, "OFFSET": offset}
        async for response in self._pages("/kws1/api.json", params, "keyword", max_pages):
            yield response

    async def product_search(
        self, query: str, *, page: int | None = None, limit: int | None = None
    ) -> APIResponse:
        """Request /productv1/api.json. See docs/api-reference.md."""
        params: Params = {"QUERY": query, "PAGE": page, "LIMIT": limit}
        return await self._request("/productv1/api.json", params, public=False)

    async def product_search_pages(
        self, query: str, *, page: int | None = None, limit: int | None = None, max_pages: int = 100
    ) -> AsyncIterator[APIResponse]:
        """Iterate response pages from /productv1/api.json. See docs/api-reference.md."""
        params: Params = {"QUERY": query, "PAGE": page, "LIMIT": limit}
        async for response in self._pages("/productv1/api.json", params, "product", max_pages):
            yield response

    async def vector_search(self, query: str, *, limit: int | None = None) -> APIResponse:
        """Request /vector/v1/api.json. See docs/api-reference.md."""
        if limit is not None and (isinstance(limit, bool) or not 1 <= limit <= 100):
            raise ValueError("limit must be between 1 and 100")
        params: Params = {"QUERY": query, "LIMIT": limit}
        return await self._request("/vector/v1/api.json", params, public=False)

    async def mcp_registry(
        self, *, search: str | None = None, category: str | None = None, offset: int | None = None
    ) -> APIResponse:
        """Request /mcp2/api.json. See docs/api-reference.md."""
        if not search and not category:
            raise ValueError("search or category is required")
        params: Params = {"SEARCH": search, "CATEGORY": category, "OFFSET": offset}
        return await self._request("/mcp2/api.json", params, public=False)

    async def mcp_registry_pages(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        offset: int | None = None,
        max_pages: int = 100,
    ) -> AsyncIterator[APIResponse]:
        """Iterate response pages from /mcp2/api.json. See docs/api-reference.md."""
        if not search and not category:
            raise ValueError("search or category is required")
        params: Params = {"SEARCH": search, "CATEGORY": category, "OFFSET": offset}
        async for response in self._pages("/mcp2/api.json", params, "registry", max_pages):
            yield response

    async def vat(self, lookup: str | list[str]) -> APIResponse:
        """Request /vat1/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": validate_lookup(lookup)}
        return await self._request("/vat1/api.json", params, public=False)

    async def trust(self, lookup: str, *, live: bool | None = None) -> APIResponse:
        """Request /trustv2/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": validate_lookup(lookup, 1), "LIVE": live}
        return await self._request("/trustv2/api.json", params, public=False)

    async def free(self, lookup: str) -> APIResponse:
        """Request /free1/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": lookup}
        return await self._request("/free1/api.json", params, public=False)

    async def company_to_url(self, company: str) -> APIResponse:
        """Request /ctu3/api.json. See docs/api-reference.md."""
        params: Params = {"COMPANY": company}
        return await self._request("/ctu3/api.json", params, public=False)

    async def tags(self, lookup: str) -> APIResponse:
        """Request /tag1/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": lookup}
        return await self._request("/tag1/api.json", params, public=False)

    async def recommendations(self, lookup: str) -> APIResponse:
        """Request /rec1/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": lookup}
        return await self._request("/rec1/api.json", params, public=False)

    async def redirects(self, lookup: str) -> APIResponse:
        """Request /redirect1/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": lookup}
        return await self._request("/redirect1/api.json", params, public=False)

    async def keywords(self, lookup: str) -> APIResponse:
        """Request /kw2/api.json. See docs/api-reference.md."""
        params: Params = {"LOOKUP": lookup}
        return await self._request("/kw2/api.json", params, public=False)

    async def trends(self, tech: str) -> APIResponse:
        """Request /trends/v6/api.json. See docs/api-reference.md."""
        params: Params = {"TECH": tech}
        return await self._request("/trends/v6/api.json", params, public=False)

    async def whoami(self) -> APIResponse:
        """Request /whoamiv1/api.json. See docs/api-reference.md."""
        params: Params = {}
        return await self._request("/whoamiv1/api.json", params, public=False)

    async def usage(self) -> APIResponse:
        """Request /usagev2/api.json. See docs/api-reference.md."""
        params: Params = {}
        return await self._request("/usagev2/api.json", params, public=False)

    async def vat_types(self) -> APIResponse:
        """Request /vat1/types.json. See docs/api-reference.md."""
        params: Params = {}
        return await self._request("/vat1/types.json", params, public=True)

    async def mcp_categories(self) -> APIResponse:
        """Request /mcp2/categories.json. See docs/api-reference.md."""
        params: Params = {}
        return await self._request("/mcp2/categories.json", params, public=True)

    async def bulk_submit(
        self,
        lookups: list[str],
        *,
        no_meta: bool = False,
        no_pii: bool = True,
        hide_text: bool = False,
        hide_dl: bool = False,
        live_only: bool = False,
    ) -> APIResponse:
        """Submit up to 5000 domains; confirm account limit with whoami first.

        Never retried automatically: an uncertain POST may already have created a job.
        Returns either synchronous results or a 202 queued-job object.
        """
        validate_lookup(lookups, 5000)
        body: JSONValue = {
            "lookups": list(lookups),
            "options": {
                "noMeta": no_meta,
                "noPii": no_pii,
                "hideText": hide_text,
                "hideDL": hide_dl,
                "liveOnly": live_only,
            },
        }
        return await self._request("/v23/domain/bulk", body=body, retry=False)

    async def bulk_status(self, job_id: str) -> APIResponse:
        """Read job status; job_id must be a UUID."""
        job = str(UUID(job_id))
        return await self._request(f"/v23/domain/bulk/{job}")

    async def bulk_result(self, job_id: str) -> APIResponse:
        """Retrieve and consume a job result. Store it: successful access deletes it.

        Never retried automatically because the server may have consumed the result.
        """
        job = str(UUID(job_id))
        return await self._request(f"/v23/domain/bulk/{job}/result", retry=False)
