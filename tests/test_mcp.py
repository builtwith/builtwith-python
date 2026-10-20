import json

import httpx
import pytest

pytest.importorskip("mcp")

from builtwith_official import AuthenticationError
from builtwith_official.mcp import MCP_URL, connect_mcp


class MCPTransport(httpx.AsyncBaseTransport):
    def __init__(self, sse=False):
        self.requests = []
        self.closed = False
        self.sse = sse

    async def handle_async_request(self, request):
        self.requests.append(request)
        assert str(request.url) == MCP_URL
        assert request.headers["Authorization"] == "Bearer test-key"
        if request.method == "GET":
            return httpx.Response(405)
        body = json.loads(request.content)
        method = body["method"]
        if "id" not in body:
            return httpx.Response(202)
        if method == "initialize":
            result = {
                "protocolVersion": body["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "Existing BuiltWith MCP", "version": "1"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "domain-api",
                        "description": "Existing domain lookup tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"lookup": {"type": "string"}},
                        },
                    }
                ]
            }
        else:
            assert method == "tools/call"
            assert body["params"]["name"] == "domain-api"
            result = {
                "content": [{"type": "text", "text": '{"Results": [], "future": true}'}],
                "isError": body["params"]["arguments"]["lookup"] == "invalid",
            }
        payload = {"jsonrpc": "2.0", "id": body["id"], "result": result}
        if self.sse:
            return httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                content="event: message\ndata: " + json.dumps(payload) + "\n\n",
            )
        return httpx.Response(200, json=payload)

    async def aclose(self):
        self.closed = True


@pytest.mark.parametrize("sse", [False, True])
async def test_existing_mcp_protocol(sse):
    transport = MCPTransport(sse)
    async with connect_mcp("test-key", transport=transport) as session:
        tools = await session.list_tools()
        assert [tool.name for tool in tools.tools] == ["domain-api"]
        result = await session.call_tool("domain-api", {"lookup": "example.com"})
        assert not result.isError
        assert json.loads(result.content[0].text)["future"] is True
        failed = await session.call_tool("domain-api", {"lookup": "invalid"})
        assert failed.isError
    assert transport.closed
    assert all("KEY" not in r.url.params for r in transport.requests)


async def test_mcp_environment_and_cleanup(monkeypatch):
    monkeypatch.setenv("BUILTWITH_API_KEY", "test-key")
    transport = MCPTransport()
    async with connect_mcp(transport=transport) as session:
        assert (await session.list_tools()).tools
    assert transport.closed


async def test_mcp_missing_key(monkeypatch):
    monkeypatch.delenv("BUILTWITH_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        async with connect_mcp():
            pytest.fail("Must not connect without credentials")
    with pytest.raises(ValueError):
        async with connect_mcp("bad\r\nkey"):
            pytest.fail("Must reject header injection")
