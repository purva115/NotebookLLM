"""
chat_service.py — RAG-powered chat with Gemini.
Chat history is persisted to messages.jsonl (spec requirement) via notebook_store.
SQLite is kept for fast structured queries (ChatMessage ORM model still used).
"""
from typing import List, Tuple

from app.services.retrieval.vector_search import build_context
from app.services.llm.client import generate_rag_answer
from app.services.storage import notebook_store
from app.db.session import get_db
from app.db import crud


def chat(
    username: str,
    notebook_id: str,
    user_question: str,
    gradio_history: list,
) -> Tuple[str, List[str]]:
    """
    Full RAG chat turn.

    Args:
        username:       HF username (used for filesystem isolation).
        notebook_id:    Current notebook's UUID.
        user_question:  User's question string.
        gradio_history: Gradio chatbot history [[user, assistant], ...]

    Returns:
        (answer_string, cited_chunk_ids)
    """
    # 1. Retrieve context from per-notebook ChromaDB
    context, cited_ids = build_context(username, notebook_id, user_question)

    if not context:
        return (
            "⚠️ No relevant content found in your sources. "
            "Please add sources to this notebook first."
        ), []

    # 2. Convert Gradio history to model format (last 5 turns)
    history = []
    for pair in gradio_history[-5:]:
        if pair[0]:
            history.append({"role": "user", "content": pair[0]})
        if pair[1]:
            history.append({"role": "model", "content": pair[1]})

    # 3. Generate grounded answer
    answer = generate_rag_answer(user_question, context, history)

    # 4a. Persist to messages.jsonl (spec-required filesystem store)
    notebook_store.append_chat_message(
        username, notebook_id, "user", user_question
    )
    notebook_store.append_chat_message(
        username, notebook_id, "assistant", answer, cited_ids=cited_ids
    )

    # 4b. Also persist to SQLite for fast structured queries
    with get_db() as db:
        crud.save_message(db, notebook_id, "user", user_question)
        crud.save_message(db, notebook_id, "assistant", answer, cited_chunk_ids=cited_ids)

    return answer, cited_ids


def load_chat_history(username: str, notebook_id: str) -> List[dict]:
    """
    Load full chat history for a notebook from messages.jsonl.
    Returns list of {role, content, cited_ids, timestamp} dicts.
    """
    return notebook_store.read_chat_history(username, notebook_id)
