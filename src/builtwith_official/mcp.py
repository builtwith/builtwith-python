"""Optional client integration with the existing hosted BuiltWith MCP server."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from .exceptions import AuthenticationError

MCP_URL = "https://api.builtwith.com/mcp"


@asynccontextmanager
async def connect_mcp(
    api_key: str | None = None,
    *,
    timeout: float = 30.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> AsyncIterator[ClientSession]:
    """Initialize a session with BuiltWith's existing streamable HTTP MCP server.

    Requires the mcp extra. Uses BUILTWITH_API_KEY unless explicitly overridden.
    Yields the official MCP ClientSession for tool/prompt/resource discovery and calls.
    Connections and the supplied transport are closed on exit. No automatic retries
    are added to potentially credit-consuming tool calls. MCP protocol errors and
    tool result isError semantics are preserved by the official MCP client library.
    """
    key = api_key if api_key is not None else os.environ.get("BUILTWITH_API_KEY", "")
    if not key.strip():
        raise AuthenticationError("Set BUILTWITH_API_KEY or pass api_key")
    if any(c in key for c in ("\r", "\n")):
        raise ValueError("Invalid API key")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    async with httpx.AsyncClient(
        headers={"Authorization": "Bearer " + key},
        timeout=timeout,
        transport=transport,
        follow_redirects=False,
        trust_env=False,
    ) as http:
        async with streamable_http_client(MCP_URL, http_client=http) as (reader, writer, _):
            async with ClientSession(
                reader, writer, read_timeout_seconds=timedelta(seconds=timeout)
            ) as session:
                await session.initialize()
                yield session
