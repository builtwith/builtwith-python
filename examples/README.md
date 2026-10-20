# Python SDK examples

Install the SDK with `pip install builtwith-official` (or `pip install .` from its root). Set `BUILTWITH_API_KEY` for authenticated methods.

| File | Purpose | Extra dependencies |
| --- | --- | --- |
| `agent_tools.py` | Annotated functions; runnable demo only calls public VAT types | None |
| `async_lookup.py` | Async lookup, also usable with top-level await in notebooks | None |
| `pipeline.py` | Bounded Lists export to JSONL | None; Lists subscription required |
| `framework_tools.py` | LangChain/LlamaIndex tool factories, no LLM calls | `langchain-core` or `llama-index-core` |
| `fastapi_app.py` | Async client shared through application lifespan | `fastapi`, ASGI server |

Importing these examples performs no requests. `async_lookup.py` deliberately performs a
credit-consuming lookup when run. The optional framework examples are illustrative adapters,
not dependencies of the SDK; verify against the framework version selected by your app.

