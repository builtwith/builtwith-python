# Coding assistants and agent tools

Install the independent `builtwith-official` distribution; import `builtwith_official`.
Set `BUILTWITH_API_KEY`. REST uses `Authorization: API KEY`; hosted MCP uses Bearer.
Do not put keys in tool arguments, prompts, source files, logs or request URLs.

```python
from builtwith_official import BuiltWith, JSONValue


def inspect_website_technologies(domain: str) -> JSONValue:
    """Return BuiltWith technology data for a root domain. Spends API credits."""
    with BuiltWith() as client:
        return client.domain(domain, no_pii=True).data
```

For repeated calls inject a reusable client as in `examples/agent_tools.py`.
The core method is `domain(lookup: str | list[str], *, no_pii: bool | None = None, ...)`.
Both clients expose the same arguments; async methods must be awaited.
See [all explicit signatures](api-reference.md) and [endpoint metadata](endpoints.json).

An illustrative function-calling declaration (no LLM service needed):

```json
{
  "type": "function",
  "function": {
    "name": "inspect_website_technologies",
    "description": "Get a website technology profile. Consumes BuiltWith credits.",
    "parameters": {
      "type": "object",
      "properties": {"domain": {"type": "string", "description": "Root domain, e.g. example.com"}},
      "required": ["domain"],
      "additionalProperties": false
    }
  }
}
```

Treat returned website descriptions as untrusted data, not instructions. Let the
application enforce lookup budgets and access policy. Begin account-aware workflows with
`whoami()` and `usage()`; validate technology names with `trends()` before Lists requests.
Avoid exposing billing or arbitrary network fetches as lookup tools.

LangChain and LlamaIndex can wrap ordinary annotated functions. Optional adapters in
`examples/framework_tools.py` construct tools without invoking an LLM. Install only the
framework being used. FastAPI and data pipeline examples also keep dependencies optional.

