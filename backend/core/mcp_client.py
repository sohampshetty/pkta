# core/mcp_client.py
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = "http://127.0.0.1:8050/sse"

async def call_mcp_tool(tool_name: str, args: dict):
    """
    Call an MCP tool and return its textual output.
    """
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=args)

            outputs = []
            for c in result.content:
                if hasattr(c, "text"):
                    outputs.append(c.text)
            return "\n".join(outputs) if outputs else str(result)
