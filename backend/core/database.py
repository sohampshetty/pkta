from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException
from core.config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION

mongo_client: Optional[AsyncIOMotorClient] = None
users_collection = None


async def connect_to_mongo():
    global mongo_client, users_collection
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[MONGO_DB_NAME]
    users_collection = db[MONGO_COLLECTION]
    print("✅ Connected to MongoDB")


async def close_mongo_connection():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("🧹 MongoDB connection closed")


async def get_user_details(user_id: str):
    try:
        query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"user_id": user_id}
        user = await users_collection.find_one(query)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": str(user.get("_id", "")),
            "name": user.get("username", "Unknown"),
            "remaining_leaves": user.get("leave_balance", 0),
            "total_leaves": user.get("total_leaves", 100),
        }
    except Exception as e:
        print(f"❌ Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Database error")
