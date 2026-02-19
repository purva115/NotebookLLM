"""
embedder.py
Generates text embeddings via Google's text-embedding-004 model.
"""
from typing import List

import google.generativeai as genai

from app.core.config import GOOGLE_API_KEY, EMBEDDING_MODEL

genai.configure(api_key=GOOGLE_API_KEY)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of text strings using Google's embedding model.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (list of floats).
    """
    if not texts:
        return []

    # Google API batches up to 100 texts at a time
    embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=batch,
            task_type="retrieval_document",
        )
        embeddings.extend(result["embedding"])

    return embeddings


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string (uses task_type=retrieval_query for better retrieval accuracy).
    """
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]
