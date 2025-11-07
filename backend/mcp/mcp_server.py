import asyncio
import os
from mcp.server.fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

# ---- Load Environment Variables ----
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "hr_assistant")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "users")

# ---- MCP Server ----
mcp = FastMCP("HRMCPServer", host="127.0.0.1", port=8050)

# ---- MongoDB Setup ----
mongo_client = None
users_collection = None


async def connect_to_mongo():
    """Initialize MongoDB connection."""
    global mongo_client, users_collection
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(MONGO_URI)
        db = mongo_client[MONGO_DB_NAME]
        users_collection = db[MONGO_COLLECTION]
        print(f"✅ Connected to MongoDB: {MONGO_URI}")


async def close_mongo_connection():
    """Close MongoDB connection."""
    global mongo_client
    if mongo_client is not None:
        mongo_client.close()
        print("🧹 MongoDB connection closed")


# ---- MCP Tools ----

@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone."""
    return f"👋 Hello, {name}! Nice to meet you."


@mcp.tool()
async def add_user(username: str, leave_balance: int = 10, total_leaves: int = 100) -> str:
    """
    Add a new user to MongoDB.
    Returns the newly created user ID.
    """
    global users_collection
    if users_collection is None:
        await connect_to_mongo()

    user_doc = {
        "username": username,
        "leave_balance": leave_balance,
        "total_leaves": total_leaves,
    }

    result = await users_collection.insert_one(user_doc)
    return f"✅ User '{username}' added with ID: {result.inserted_id}"


@mcp.tool()
async def get_user(user_id: str) -> str:
    """
    Fetch a user's details from MongoDB.
    """
    global users_collection
    if users_collection is None:
        await connect_to_mongo()

    query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"user_id": user_id}
    user = await users_collection.find_one(query)

    if not user:
        return f"❌ User not found for ID: {user_id}"

    return (
        f"👤 Name: {user.get('username', 'Unknown')}\n"
        f"🌿 Remaining Leaves: {user.get('leave_balance', 0)}\n"
        f"📅 Total Leaves: {user.get('total_leaves', 100)}"
    )

@mcp.tool()
async def list_users(limit: int = 10) -> str:
    """
    List the most recent users from MongoDB.
    """
    global users_collection
    if users_collection is None:
        await connect_to_mongo()

    cursor = users_collection.find().sort("_id", -1).limit(limit)
    users = await cursor.to_list(length=limit)

    if not users:
        return "📭 No users found in the database."

    lines = ["👥 Latest Users:"]
    for user in users:
        lines.append(
            f"- ID: {user.get('_id')}, "
            f"Name: {user.get('username', 'Unknown')}, "
            f"Leaves: {user.get('leave_balance', 0)}/{user.get('total_leaves', 100)}"
        )

    return "\n".join(lines)

@mcp.tool()
async def update_leave_balance(user_id: str, new_balance: int) -> str:
    """
    Update a user's leave balance.
    """
    global users_collection
    if users_collection is None:
        await connect_to_mongo()

    query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"user_id": user_id}
    result = await users_collection.update_one(query, {"$set": {"leave_balance": new_balance}})

    if result.modified_count == 0:
        return f"⚠️ No user found or balance unchanged for ID: {user_id}"
    return f"✅ Updated leave balance to {new_balance} for user ID: {user_id}"


@mcp.tool()
async def delete_user(user_id: str) -> str:
    """
    Delete a user from MongoDB.
    """
    global users_collection
    if users_collection is None:
        await connect_to_mongo()

    query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"user_id": user_id}
    result = await users_collection.delete_one(query)

    if result.deleted_count == 0:
        return f"❌ No user found for ID: {user_id}"
    return f"🗑️ Deleted user with ID: {user_id}"


# ---- Startup & Shutdown ----

async def startup():
    await connect_to_mongo()

async def shutdown():
    await close_mongo_connection()


if __name__ == "__main__":
    try:
        asyncio.run(startup())
        mcp.run(transport="sse")  # Server-Sent Events transport
    finally:
        asyncio.run(shutdown())
