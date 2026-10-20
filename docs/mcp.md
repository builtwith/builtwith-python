# Integration with the existing BuiltWith MCP server

Python connects to the existing official endpoint at `https://api.builtwith.com/mcp`.
This package does not create or host another MCP server.

## Python client

```bash
pip install "builtwith-official[mcp]"
```

Set `BUILTWITH_API_KEY` in your environment. Then use the official MCP Python
client session through the SDK connection helper:

```python
import asyncio
from builtwith_official.mcp import connect_mcp


async def main() -> None:
    async with connect_mcp() as session:
        tools = await session.list_tools()
        print([tool.name for tool in tools.tools])
        # No credits spent by discovery. This lookup uses API credits:
        result = await session.call_tool("domain-api", {"lookup": "example.com"})
        if result.isError:
            print("BuiltWith tool returned an error")
        else:
            print(result.content)


if __name__ == "__main__":
    asyncio.run(main())
```

Signature:

```python
connect_mcp(api_key: str | None = None, *, timeout: float = 30.0,
            transport: httpx.AsyncBaseTransport | None = None)
```

Returns an async context manager yielding `mcp.ClientSession`. Initialization and
connection cleanup are automatic. The supplied transport is owned and closed.
Authentication uses `Authorization: Bearer KEY`, matching the existing Node and .NET
AI SDKs. No key is added to URLs. The core REST clients remain independent of MCP.

Use `session.list_tools()` to discover the existing server's current names and input
schemas. Existing examples include `domain-api` with `lookup`, `domain-lookup` with
`domain`, `trends-api` with `tech`, and `usage-api` with no arguments. Pass a discovery
result's `nextCursor` to `session.list_tools(cursor=...)` when provided. Prompts and
resources can also be discovered through standard ClientSession methods.

Tool calls preserve `CallToolResult.content`, `structuredContent`, and `isError`.
Protocol/transport failures retain the official MCP library exception semantics,
including exception groups from its task groups. No automatic application retry is
added because tool calls may spend credits. Avoid logging authorization headers or
sensitive tool responses. Call only tools appropriate to the account and application.

## Existing MCP host configuration

For a coding assistant that connects directly, use its supported secret-store mechanism:

```json
{
  "mcpServers": {
    "builtwith": {
      "url": "https://api.builtwith.com/mcp",
      "headers": {"Authorization": "Bearer YOUR_BUILTWITH_API_KEY"}
    }
  }
}
```

The hosted endpoint uses streamable HTTP and accepts POST. It is already public;
no new server deployment is required. The MCP registry REST search (`/mcp2/api.json`)
is a different API for discovering remote MCP services. The existing server project
remains [builtwith/builtwith-mcp](https://github.com/builtwith/builtwith-mcp).
