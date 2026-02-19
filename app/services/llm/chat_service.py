"""
chat_service.py — RAG-powered chat with Gemini and conversation history.
"""
from typing import List, Tuple

from app.services.retrieval.vector_search import build_context
from app.services.llm.client import generate_rag_answer
from app.db.session import get_db
from app.db import crud


def chat(notebook_id: str, user_question: str,
         gradio_history: list) -> Tuple[str, List[str]]:
    """
    Full RAG chat turn.

    Args:
        notebook_id:    Current notebook's ID.
        user_question:  User's question string.
        gradio_history: Gradio chatbot history [[user, assistant], ...]

    Returns:
        (answer_string, cited_chunk_ids)
    """
    # 1. Retrieve context from ChromaDB
    context, cited_ids = build_context(notebook_id, user_question)

    if not context:
        return ("⚠️ No relevant content found in your sources. "
                "Please add sources to this notebook first."), []

    # 2. Convert Gradio history to Gemini format
    history = []
    for pair in gradio_history[-5:]:  # last 5 turns
        if pair[0]:
            history.append({"role": "user", "content": pair[0]})
        if pair[1]:
            history.append({"role": "model", "content": pair[1]})

    # 3. Generate grounded answer
    answer = generate_rag_answer(user_question, context, history)

    # 4. Persist both messages to SQLite
    with get_db() as db:
        crud.save_message(db, notebook_id, "user", user_question)
        crud.save_message(db, notebook_id, "assistant", answer, cited_chunk_ids=cited_ids)

    return answer, cited_ids
