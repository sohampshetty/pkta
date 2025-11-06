from fastapi import APIRouter, HTTPException
from core.intent_detection import detect_intent, detect_intent_llm
from core.llm_utils import retriever, build_prompt_from_docs, call_llm
from core.database import get_user_details
from models.hr_models import QueryRequest, QueryResponse

router = APIRouter(prefix="/hr", tags=["HR Assistant"])


@router.post("/query", response_model=QueryResponse)
async def handle_query(req: QueryRequest):
    query = req.query.strip()
    if not query:
        return QueryResponse(mode="error", intent="none", answer="Empty query provided.")

    intent = detect_intent_llm(query)
    print(f"🧠 Detected intent: {intent}")

    # ---- Leave Balance ----
    if intent == "leave_balance":
        if not req.user_id:
            return QueryResponse(mode="API", intent=intent, answer="User ID is required.")
        try:
            user = await get_user_details(req.user_id)
        except HTTPException as e:
            return QueryResponse(mode="API", intent=intent, answer=e.detail)

        prompt = f"""
        The user asked: "{req.query}"
        HR Database:
        - Name: {user['name']}
        - Remaining Leaves: {user['remaining_leaves']}
        - Total Leaves: {user['total_leaves']}

        Write a friendly response explaining their leave balance.
        """
        answer = call_llm(prompt)
        return QueryResponse(mode="LLM+DB", intent=intent, answer=answer)

    # ---- Policy Query ----
    if intent == "policy_query" and retriever:
        try:
            docs = retriever.invoke(query)
        except Exception:
            docs = retriever.get_relevant_documents(query)
        if not docs:
            return QueryResponse(mode="RAG", intent=intent, answer="No relevant HR documents found.")
        prompt = build_prompt_from_docs(docs, query)
        answer = call_llm(prompt)
        return QueryResponse(mode="RAG", intent=intent, answer=answer)

    # ---- Fallback ----
    answer = call_llm(query)
    return QueryResponse(mode="Direct LLM", intent=intent, answer=answer)


@router.get("/")
def hr_root():
    return {"status": "ok", "module": "HR Assistant", "intent_detection": True}
