# API reference

Both clients expose the signatures below. `AsyncBuiltWith` methods are awaited;
its `*_pages` methods return async iterators. Constructor transports are
`httpx.BaseTransport` (sync) or `httpx.AsyncBaseTransport` (async).

`APIResponse.data` is recursive JSON; `headers`, `status_code`, and `content` retain
response metadata and raw bytes. Methods raise SDK exceptions for HTTP/application errors.

## Explicit signatures

```python
def __init__(self, api_key: str | None=None, *, timeout: float | httpx.Timeout=30.0, max_retries: int=0, backoff_factor: float=0.5, max_retry_after: float=120.0, transport: httpx.BaseTransport | None=None) -> None ...
```



```python
def close(self) -> None ...
```

Close pooled connections and the supplied transport.

```python
def domain(self, lookup: str | list[str], *, hide_text: bool | None=None, hide_dl: bool | None=None, live_only: bool | None=None, no_meta: bool | None=None, no_pii: bool | None=None, no_attr: bool | None=None, ip: bool | None=None, trust: bool | None=None, first_detected: str | None=None, last_detected: str | None=None) -> APIResponse ...
```

Request /v26/api.json. See docs/api-reference.md.

```python
def changes(self, lookup: str | list[str], *, since: str | None=None) -> APIResponse ...
```

Request /change1/api.json. See docs/api-reference.md.

```python
def relationships(self, lookup: str, *, page: int | None=None, ip: bool | None=None) -> APIResponse ...
```

Request /rv5/api.json. See docs/api-reference.md.

```python
def relationships_pages(self, lookup: str, *, page: int | None=None, ip: bool | None=None, max_pages: int=100) -> Iterator[APIResponse] ...
```

Iterate response pages from /rv5/api.json. See docs/api-reference.md.

```python
def lists(self, tech: str, *, offset: str | None=None, country: str | None=None, since: str | None=None, all_sites: bool | None=None, meta: bool | None=None, other_techs: str | None=None, spend: str | None=None, revenue: str | None=None, sku: str | None=None, followers: str | None=None, employees: str | None=None, sitemap: str | None=None, pagerank: str | None=None, bwrank: str | None=None, tranco: str | None=None, majestic: str | None=None, bws: str | None=None, ecat: str | None=None, aim: str | None=None, aio: str | None=None, air: str | None=None, aiv: str | None=None) -> APIResponse ...
```

Request /lists13/api.json. See docs/api-reference.md.

```python
def lists_pages(self, tech: str, *, offset: str | None=None, country: str | None=None, since: str | None=None, all_sites: bool | None=None, meta: bool | None=None, other_techs: str | None=None, spend: str | None=None, revenue: str | None=None, sku: str | None=None, followers: str | None=None, employees: str | None=None, sitemap: str | None=None, pagerank: str | None=None, bwrank: str | None=None, tranco: str | None=None, majestic: str | None=None, bws: str | None=None, ecat: str | None=None, aim: str | None=None, aio: str | None=None, air: str | None=None, aiv: str | None=None, max_pages: int=100) -> Iterator[APIResponse] ...
```

Iterate response pages from /lists13/api.json. See docs/api-reference.md.

```python
def ask(self, query: str, *, commit: bool | None=None, next_offset: str | None=None, meta: bool | None=None) -> APIResponse ...
```

Request /ask1/api.json. See docs/api-reference.md.

```python
def ask_pages(self, query: str, *, commit: bool | None=None, next_offset: str | None=None, meta: bool | None=None, max_pages: int=100) -> Iterator[APIResponse] ...
```

Iterate response pages from /ask1/api.json. See docs/api-reference.md.

```python
def keyword_search(self, keyword: str, *, limit: int | None=None, offset: str | None=None) -> APIResponse ...
```

Request /kws1/api.json. See docs/api-reference.md.

```python
def keyword_search_pages(self, keyword: str, *, limit: int | None=None, offset: str | None=None, max_pages: int=100) -> Iterator[APIResponse] ...
```

Iterate response pages from /kws1/api.json. See docs/api-reference.md.

```python
def product_search(self, query: str, *, page: int | None=None, limit: int | None=None) -> APIResponse ...
```

Request /productv1/api.json. See docs/api-reference.md.

```python
def product_search_pages(self, query: str, *, page: int | None=None, limit: int | None=None, max_pages: int=100) -> Iterator[APIResponse] ...
```

Iterate response pages from /productv1/api.json. See docs/api-reference.md.

```python
def vector_search(self, query: str, *, limit: int | None=None) -> APIResponse ...
```

Request /vector/v1/api.json. See docs/api-reference.md.

```python
def mcp_registry(self, *, search: str | None=None, category: str | None=None, offset: int | None=None) -> APIResponse ...
```

Request /mcp2/api.json. See docs/api-reference.md.

```python
def mcp_registry_pages(self, *, search: str | None=None, category: str | None=None, offset: int | None=None, max_pages: int=100) -> Iterator[APIResponse] ...
```

Iterate response pages from /mcp2/api.json. See docs/api-reference.md.

```python
def vat(self, lookup: str | list[str]) -> APIResponse ...
```

Request /vat1/api.json. See docs/api-reference.md.

```python
def trust(self, lookup: str, *, live: bool | None=None) -> APIResponse ...
```

Request /trustv2/api.json. See docs/api-reference.md.

```python
def free(self, lookup: str) -> APIResponse ...
```

Request /free1/api.json. See docs/api-reference.md.

```python
def company_to_url(self, company: str) -> APIResponse ...
```

Request /ctu3/api.json. See docs/api-reference.md.

```python
def tags(self, lookup: str) -> APIResponse ...
```

Request /tag1/api.json. See docs/api-reference.md.

```python
def recommendations(self, lookup: str) -> APIResponse ...
```

Request /rec1/api.json. See docs/api-reference.md.

```python
def redirects(self, lookup: str) -> APIResponse ...
```

Request /redirect1/api.json. See docs/api-reference.md.

```python
def keywords(self, lookup: str) -> APIResponse ...
```

Request /kw2/api.json. See docs/api-reference.md.

```python
def trends(self, tech: str) -> APIResponse ...
```

Request /trends/v6/api.json. See docs/api-reference.md.

```python
def whoami(self) -> APIResponse ...
```

Request /whoamiv1/api.json. See docs/api-reference.md.

```python
def usage(self) -> APIResponse ...
```

Request /usagev2/api.json. See docs/api-reference.md.

```python
def vat_types(self) -> APIResponse ...
```

Request /vat1/types.json. See docs/api-reference.md.

```python
def mcp_categories(self) -> APIResponse ...
```

Request /mcp2/categories.json. See docs/api-reference.md.

```python
def bulk_submit(self, lookups: list[str], *, no_meta: bool=False, no_pii: bool=True, hide_text: bool=False, hide_dl: bool=False, live_only: bool=False) -> APIResponse ...
```

Submit up to 5000 domains; confirm account limit with whoami first.

Never retried automatically: an uncertain POST may already have created a job.
Returns either synchronous results or a 202 queued-job object.

```python
def bulk_status(self, job_id: str) -> APIResponse ...
```

Read job status; job_id must be a UUID.

```python
def bulk_result(self, job_id: str) -> APIResponse ...
```

Retrieve and consume a job result. Store it: successful access deletes it.

Never retried automatically because the server may have consumed the result.

## Parameter conventions

`lookup` is a domain or, where typed as a list, a batch. Domain/VAT batches are limited
to 16; Relationships accepts one domain. Bulk submit checks 1–5000; confirm the account
limit with WhoAmI. Empty required strings are rejected. No DNS/network validation occurs.

Optional parameters default to omitted. Boolean flags serialize as yes/no; Ask commit
uses true/false. The parameter mapping is recorded in endpoints.json. `first_detected`
and `last_detected` map to FDRANGE/LDRANGE and accept YYYY-MM-DD|YYYY-MM-DD.

Lists numeric filters (`spend`, `revenue`, `employees`, etc.) accept strings such as
"100|GT" or "50|GTE"; supported operators: EQ, LT, LTE, GT, GTE. `all_sites=True` cannot
be combined with `since`. `other_techs` accepts comma-separated names (up to 16 upstream).
Country filters accept comma-separated codes. Use canonical technology names from Trends.

`changes(since=...)` accepts natural dates; server default is three months. Vector limit
is 1–100; Keyword Search limit is 16–1000. Registry requires search and/or category.

Pagination preserves initial filters. Lists and Keyword Search send OFFSET, Ask sends
NEXTOFFSET, Relationships sends PAGE, Registry reads header pagination, and Product
extracts PAGE/LIMIT from next_page. Helpers return pages, not flattened records; this
preserves relationship identifier groupings and unexpected response fields.

For access, cost and bulk lifecycle details see README.md. Unknown fields remain intact.
