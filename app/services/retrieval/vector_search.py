"""
vector_search.py
Retrieves top-K relevant chunks from the per-notebook ChromaDB given a user query,
then formats them into a prompt context string with citations.
"""
from typing import List, Tuple

from app.core.config import TOP_K_CHUNKS
from app.services.ingestion.embedder import embed_query
from app.services.storage import notebook_store


def vector_search(
    username: str,
    notebook_id: str,
    query: str,
    top_k: int = TOP_K_CHUNKS,
) -> List[dict]:
    """
    Embed query and search the notebook's ChromaDB collection.

    Returns:
        List of dicts: [{id, content, source_id, chunk_index, distance}]
    """
    collection = notebook_store.get_chroma_collection(username, notebook_id)

    if collection.count() == 0:
        return []

    query_vec = embed_query(query)
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for i, doc_id in enumerate(results["ids"][0]):
        hits.append({
            "id": doc_id,
            "content": results["documents"][0][i],
            "source_id": results["metadatas"][0][i].get("source_id"),
            "chunk_index": results["metadatas"][0][i].get("chunk_index"),
            "distance": results["distances"][0][i],
        })
    return hits


def build_context(
    username: str,
    notebook_id: str,
    query: str,
) -> Tuple[str, List[str]]:
    """
    Build the context string for the LLM prompt and collect cited chunk IDs.

    Returns:
        (context_string, list_of_cited_chunk_ids)
    """
    hits = vector_search(username, notebook_id, query)
    if not hits:
        return "", []

    context_parts = []
    cited_ids = []
    for i, hit in enumerate(hits, start=1):
        context_parts.append(f"[{i}] {hit['content']}")
        cited_ids.append(hit["id"])

    context = "\n\n".join(context_parts)
    return context, cited_ids
