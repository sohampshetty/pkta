from fastapi import APIRouter, HTTPException
from core.intent_detection import detect_intent, detect_intent_llm
from core.llm_utils import retriever, build_prompt_from_docs, call_llm
from core.database import get_user_details
from models.hr_models import QueryRequest, QueryResponse
from core.mcp_client import call_mcp_tool
import json
import re

router = APIRouter(prefix="/hr", tags=["HR Assistant"])


@router.post("/query", response_model=QueryResponse)
async def handle_query(req: QueryRequest):
    query = req.query.strip()
    if not query:
        return QueryResponse(mode="error", intent="none", answer="Empty query provided.")

    intent = detect_intent_llm(query)
    print(f"🧠 Detected intent: {intent}")

    # --- Skip tool logic for greetings / small talk ---
    if intent in ["general", "greeting", "small_talk"]:
        answer = call_llm(query)
        return QueryResponse(mode="Direct LLM", intent=intent, answer=answer)

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

    # ---- Default / Tool Handling ----
    tool_prompt = f"""
    You are an HR assistant with access to system tools.

    Your job:
    - Use tools **only** when the user explicitly requests an action that changes or retrieves database data.
    - For casual chat, greetings, or general HR questions (like "hi", "hello", "how are you", "what can you do"), reply normally in natural language.
    - Never call tools for greetings, small talk, or general conversation.

    If you need to perform a data action (add, update, delete, list, or fetch users), respond **only** with JSON in this exact format:
    {{
      "action": "call_tool",
      "tool": "<tool_name>",
      "args": {{ "param1": <value>, "param2": <value> }}
    }}

    Otherwise, respond with plain text.

    Available tools:
      - add_user(username: str, leave_balance: int, total_leaves: int)
      - get_user(user_id: str)
      - update_leave_balance(user_id: str, new_balance: int)
      - delete_user(user_id: str)
      - list_users(limit: int)

    User query: {query}
    """

    raw_llm_response = call_llm(tool_prompt)
    print("🔍 LLM raw output:", raw_llm_response)

    # --- Clean and normalize LLM output before parsing ---
    cleaned = (
        raw_llm_response
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    # Try parsing JSON safely
    try:
        parsed = json.loads(cleaned)
    except Exception:
        parsed = None

    # --- Normalize older or imperfect outputs ---
    if isinstance(parsed, dict):
        # Case 1: model said "action": "add_user"
        if parsed.get("action") in ["add_user", "get_user", "update_leave_balance", "delete_user", "list_users"]:
            parsed = {
                "action": "call_tool",
                "tool": parsed["action"],
                "args": parsed.get("args", {})
            }

        # Case 2: model used a single string action like "list_users(limit=1)"
        elif isinstance(parsed.get("action"), str) and "(" in parsed["action"]:
            match = re.match(r"(\w+)\((.*?)\)", parsed["action"])
            if match:
                tool = match.group(1)
                args_str = match.group(2)
                args = {}
                for pair in args_str.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        args[k.strip()] = int(v.strip()) if v.strip().isdigit() else v.strip()
                parsed = {"action": "call_tool", "tool": tool, "args": args}

        # Case 3: model gave tool + args but no action
        elif "tool" in parsed and "args" in parsed and "action" not in parsed:
            parsed["action"] = "call_tool"

    # --- Execute tool if requested ---
    if isinstance(parsed, dict) and parsed.get("action") == "call_tool":
        tool = parsed.get("tool")
        args = parsed.get("args", {})
        print(f"🛠️ LLM requested tool: {tool} with args {args}")

        # Default arguments for add_user
        if tool == "add_user":
            args.setdefault("leave_balance", 10)
            args.setdefault("total_leaves", 100)

        try:
            tool_result = await call_mcp_tool(tool, args)
        except Exception as e:
            return QueryResponse(mode="MCP", intent=tool, answer=f"Tool call failed: {repr(e)}")

        # Let LLM phrase final response but include details
        final_prompt = f"""
        The tool executed successfully.

        Tool: {tool}
        Arguments: {args}

        Tool output:
        {tool_result}

        Now, write a friendly message to the user. 
        - Always include the key information from the tool output (like usernames, IDs, or leave details). 
        - Keep the tone polite and concise. 
        - Do NOT summarize vaguely like "Here’s the list" — show actual data snippets.
        """
        final_reply = call_llm(final_prompt)
        return QueryResponse(mode="MCP+LLM", intent=tool, answer=final_reply)


    # --- Otherwise, just return text ---
    return QueryResponse(mode="Direct LLM", intent=intent, answer=raw_llm_response)


@router.get("/")
def hr_root():
    return {"status": "ok", "module": "HR Assistant", "intent_detection": True}
