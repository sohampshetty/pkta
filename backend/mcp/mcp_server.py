from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("MCPServercd")

# Simple tool
@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone

    Args:
        name: The person's name to greet
    """
    return f"Hello, {name}! Nice to meet you."

# Run using uvicorn to bind correctly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        mcp.app,
        host="0.0.0.0",  # listen on all IPv4 interfaces
        port=6274,
        workers=1,
        loop="asyncio",
        http="h11"
    )