"""
chunker.py
Splits long text into overlapping windows for embedding.
"""
from typing import List


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[dict]:
    """
    Split text into overlapping word-based chunks.

    Args:
        text:       Source text to chunk.
        chunk_size: Target number of words per chunk.
        overlap:    Number of words to overlap between consecutive chunks.

    Returns:
        List of dicts: [{content, chunk_index, word_start, word_end}]
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max(1, chunk_size - overlap)
    idx = 0

    for chunk_index, start in enumerate(range(0, len(words), step)):
        end = min(start + chunk_size, len(words))
        content = " ".join(words[start:end])
        chunks.append({
            "content": content,
            "chunk_index": chunk_index,
            "word_start": start,
            "word_end": end,
        })
        if end == len(words):
            break

    return chunks
