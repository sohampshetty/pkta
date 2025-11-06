import os, textwrap
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.llms import Ollama
from core.config import FAISS_INDEX_PATH, OLLAMA_BASE_URL, LLM_MODEL

# Initialize LLM + embeddings
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
llm = Ollama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL)

# Optional FAISS retriever
retriever = None
if os.path.exists(FAISS_INDEX_PATH):
    db = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True,
    )
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 4})


def call_llm(prompt: str):
    """Safe LLM invocation"""
    try:
        return llm(prompt)
    except Exception:
        try:
            return llm.invoke(prompt)
        except Exception as e:
            return f"Error calling LLM: {repr(e)}"


def build_prompt_from_docs(docs, question, max_chars_per_doc=1200, max_total_chars=6000):
    parts, total = [], 0
    for d in docs:
        snippet = (d.page_content or "").strip().replace("\n", " ")[:max_chars_per_doc]
        source = d.metadata.get("source", d.metadata.get("filename", "unknown"))
        parts.append(f"Source: {source}\n{snippet}")
        total += len(snippet)
        if total > max_total_chars:
            break

    context = "\n\n---\n\n".join(parts)
    return textwrap.dedent(f"""
    You are a helpful HR assistant. Use the document snippets below to answer the question.
    If no answer found, say "I don't see relevant policy text in the documents."

    Context:
    {context}

    Question: {question}

    Provide:
    1) A concise answer (2–4 sentences)
    2) Bullet list of sources (filenames)
    3) If not found, say you didn’t find it.
    """).strip()
