import asyncio
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()  # Needed when running inside interactive shells

"""
✅ Make sure:
1. Your server is running with SSE transport:
       uv run mcp/mcp_server.py
2. It listens on port 8050 (default in your server)
3. Then run this client:
       uv run mcp/mcp_client.py
"""

async def main():
    # Connect to the MCP server using SSE
    async with sse_client("http://127.0.0.1:8050/sse") as (read_stream, write_stream):
        # Create MCP session
        async with ClientSession(read_stream, write_stream) as session:
            print("✅ Connected to MCP server via SSE")

            # Initialize the connection
            await session.initialize()

            # ---- List available tools ----
            tools_result = await session.list_tools()
            print("\n🧰 Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # ---- Example: Call 'add_user' ----
            result = await session.call_tool(
                "add_user",
                arguments={"username": "Soham", "leave_balance": 15, "total_leaves": 30}
            )
            print("\n✅ Tool call result:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)

            # ---- Example: List users ----
            result = await session.call_tool("list_users", arguments={"limit": 5})
            print("\n📋 Users in DB:")
            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main())
