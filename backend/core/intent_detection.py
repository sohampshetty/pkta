from sentence_transformers import SentenceTransformer, util
import textwrap
from core.llm_utils import llm

intent_model = SentenceTransformer("all-MiniLM-L6-v2")

INTENT_EXAMPLES = {
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
    ],
    "general": ["hi", "hello", "who are you", "thank you"],
}

intent_embeddings = {
    k: intent_model.encode(v, convert_to_tensor=True) for k, v in INTENT_EXAMPLES.items()
}


def detect_intent_embedding(query: str) -> str:
    q_emb = intent_model.encode(query, convert_to_tensor=True)
    scores = {intent: util.cos_sim(q_emb, emb).max().item() for intent, emb in intent_embeddings.items()}
    best_intent = max(scores, key=scores.get)
    return best_intent if scores[best_intent] > 0.55 else "unknown"


def detect_intent_llm(query: str) -> str:
    """
    Use the LLM to classify user intent reliably.
    """
    prompt = f"""
You are an intent classifier for an HR chatbot.
Classify the user's intent into exactly one of these three categories:
- leave_balance : when the user asks about remaining leaves or total leaves
- policy_query  : when the user asks about HR policies (maternity, notice period, holidays, etc.)
- general       : for greetings, small talk, or unrelated topics

User query: "{query}"

Respond with ONLY one word:
leave_balance, policy_query, or general.
Do not include explanations or punctuation.
    """.strip()

    try:
        result = llm.invoke(prompt)

        # Extract text safely from LangChain/Ollama object
        text = getattr(result, "content", str(result)).strip().lower()

        # Clean possible extra words
        for intent in ["leave_balance", "policy_query", "general"]:
            if intent in text:
                return intent

        # If LLM drifts or returns explanation, fallback
        return "general"

    except Exception as e:
        print(f"⚠️ LLM intent detection failed: {e}")
        return "general"




def detect_intent(query: str) -> str:
    intent = detect_intent_embedding(query)
    if intent == "unknown":
        intent = detect_intent_llm(query)
    return intent
