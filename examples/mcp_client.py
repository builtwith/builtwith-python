"""Discover the existing BuiltWith MCP server tools without spending lookup credits."""

import asyncio

from builtwith_official.mcp import connect_mcp


async def main() -> None:
    async with connect_mcp() as session:
        tools = await session.list_tools()
        print([tool.name for tool in tools.tools])


if __name__ == "__main__":
    asyncio.run(main())
