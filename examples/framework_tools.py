"""Optional wrappers; these factories construct tools without calling an LLM.

Install langchain-core or llama-index-core separately when using that adapter.
Keep the supplied BuiltWith client open for the tool's lifetime.
"""

from typing import Any

from builtwith_official import BuiltWith, JSONValue


def langchain_tool(client: BuiltWith) -> Any:
    from langchain_core.tools import StructuredTool

    def inspect_website(domain: str) -> JSONValue:
        """Inspect a domain's technologies. Uses BuiltWith API credits."""
        return client.domain(domain, no_pii=True).data

    return StructuredTool.from_function(inspect_website)


def llamaindex_tool(client: BuiltWith) -> Any:
    from llama_index.core.tools import FunctionTool

    def inspect_website(domain: str) -> JSONValue:
        """Inspect a domain's technologies. Uses BuiltWith API credits."""
        return client.domain(domain, no_pii=True).data

    return FunctionTool.from_defaults(fn=inspect_website)
