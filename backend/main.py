from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import connect_to_mongo, close_mongo_connection
from routes import items, hr_assistant
import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
PORT = os.getenv("PORT", "8000")

app = FastAPI(title="Unified Backend API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(items.router)
app.include_router(hr_assistant.router)

@app.on_event("startup")
async def on_startup():
    await connect_to_mongo()
    print(f"🚀 Backend is running on http://127.0.0.1:{PORT}")

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongo_connection()

@app.get("/")
def root():
    return {
        "message": "Backend up and running!",
        "routes": ["/items", "/hr/query"],
    }
