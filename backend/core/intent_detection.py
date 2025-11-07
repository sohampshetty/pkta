from sentence_transformers import SentenceTransformer, util
from core.llm_utils import llm
import textwrap

# --- Initialize embedding model ---
intent_model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Intent examples for embedding-based fallback ---
INTENT_EXAMPLES = {
    "add_user": [
        "add a new employee",
        "create user record",
        "register a new user",
        "add john to the database",
    ],
    "update_leave_balance": [
        "update leave for john",
        "reduce leaves",
        "change leave balance",
        "update remaining leaves",
    ],
    "delete_user": [
        "remove employee",
        "delete user john",
        "remove record",
        "terminate employee",
    ],
    "list_users": [
        "show all users",
        "list employees",
        "display user list",
        "get all users",
    ],
    "get_user": [
        "get details of john",
        "fetch employee info",
        "show user data",
    ],
    "leave_balance": [
        "how many leaves left",
        "check my leave balance",
        "remaining leave days",
        "paid leaves",
    ],
    "policy_query": [
        "maternity policy",
        "notice period",
        "holiday list",
        "bonus rules",
        "working hours",
    ],
    "general": [
        "hi",
        "hello",
        "who are you",
        "thank you",
        "good morning",
        "bye",
        "how are you",
        "what can you do",
    ],
}

# --- Precompute embeddings ---
intent_embeddings = {
    k: intent_model.encode(v, convert_to_tensor=True) for k, v in INTENT_EXAMPLES.items()
}


def detect_intent_embedding(query: str) -> str:
    """
    Lightweight semantic similarity fallback for short user inputs.
    """
    q_emb = intent_model.encode(query, convert_to_tensor=True)
    scores = {intent: util.cos_sim(q_emb, emb).max().item() for intent, emb in intent_embeddings.items()}
    best_intent = max(scores, key=scores.get)
    return best_intent if scores[best_intent] > 0.55 else "unknown"


def detect_intent_llm(query: str) -> str:
    """
    Use local LLM (Ollama) for high-level intent classification.
    """

    prompt = textwrap.dedent(f"""
    You are an intent classifier for an HR assistant that can use database tools.
    Your job is to decide what the user wants to do, and return ONE label.

    Choose one of these intents:
    - add_user
    - update_leave_balance
    - delete_user
    - list_users
    - get_user
    - leave_balance
    - policy_query
    - general

    ### Rules
    - If the user asks to *add, create, register, or onboard* an employee → add_user
    - If the user wants to *update or modify leave balance* → update_leave_balance
    - If the user asks to *remove, terminate, or delete* a user → delete_user
    - If the user asks to *see, list, or show* users → list_users
    - If the user asks to *get or fetch* info for a specific employee → get_user
    - If the user asks about *remaining leaves, total leaves* → leave_balance
    - If the user asks about *HR policies* like maternity, notice period, holidays, etc. → policy_query
    - If the user greets, thanks, or makes small talk → general

    ### Examples
    "Add new user John" → add_user
    "How many leaves do I have?" → leave_balance
    "Show me all users" → list_users
    "Delete employee Mary" → delete_user
    "Update leave for John to 12" → update_leave_balance
    "What is the maternity policy?" → policy_query
    "Hello there" → general

    Now, classify this user query:
    "{query}"

    Respond with ONLY one word:
    add_user, update_leave_balance, delete_user, list_users, get_user, leave_balance, policy_query, or general.
    No punctuation. No explanation.
    """)

    try:
        result = llm.invoke(prompt)

        # Extract content safely from LangChain Ollama wrapper
        text = getattr(result, "content", str(result)).strip().lower()

        # Clean common noise
        for intent in [
            "add_user",
            "update_leave_balance",
            "delete_user",
            "list_users",
            "get_user",
            "leave_balance",
            "policy_query",
            "general",
        ]:
            if intent in text:
                return intent

        return "general"

    except Exception as e:
        print(f"⚠️ LLM intent detection failed: {e}")
        return "general"


def detect_intent(query: str) -> str:
    """
    Hybrid approach: fast embedding-based fallback + LLM refinement.
    """
    # Quick vector similarity first (for short commands)
    intent = detect_intent_embedding(query)
    if intent == "unknown":
        intent = detect_intent_llm(query)
    return intent
