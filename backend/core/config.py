import os
from dotenv import load_dotenv

load_dotenv()

# LLM + FAISS
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.31.152:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:1b")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_hr_policy_index")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://192.168.31.152:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "hr_assistant")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "users")

# APIs
LEAVE_BALANCE_API = os.getenv("LEAVE_BALANCE_API", "http://localhost:8080/user")
