# mcp_server.py
from mcp.server.fastmcp import FastMCP
from mcp.server.adapters.fastapi import asgi_app  # ✅ ASGI adapter for MCP v1.x
from pymongo import MongoClient
import uvicorn

# Create MCP server
mcp = FastMCP("hr_mcp_server")

# MongoDB setup
mongo_uri = "mongodb://192.168.31.152:27017"
client = MongoClient(mongo_uri)
db = client["hr_assistant"]
users = db["users"]

@mcp.tool()
def add_user_with_leaves(name: str, remaining_leaves: int) -> dict:
    """Add a user with leave balance to MongoDB."""
    user = {"name": name, "remaining_leaves": remaining_leaves}
    result = users.insert_one(user)
    print(f"[✅] Added user {name} with {remaining_leaves} leaves (ID: {result.inserted_id})")
    return {"id": str(result.inserted_id), **user}


if __name__ == "__main__":
    print("🚀 Starting MCP Server at http://localhost:8001")
    app = asgi_app(mcp)  # ✅ wrap FastMCP into an ASGI app
    uvicorn.run(app, host="0.0.0.0", port=8001)
