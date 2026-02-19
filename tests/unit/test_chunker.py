"""
test_chunker.py — Unit tests for text chunking.
"""
from app.services.ingestion.chunker import chunk_text


def test_empty_text():
    assert chunk_text("") == []


def test_single_chunk():
    text = " ".join(["word"] * 100)
    chunks = chunk_text(text, chunk_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0


def test_multiple_chunks():
    text = " ".join(["word"] * 1200)
    chunks = chunk_text(text, chunk_size=512, overlap=64)
    assert len(chunks) > 1
    # Check overlap: last words of chunk N appear in chunk N+1
    for i in range(len(chunks) - 1):
        c_words = chunks[i]["content"].split()
        next_words = chunks[i + 1]["content"].split()
        assert c_words[-1] in next_words


def test_chunk_indices_are_sequential():
    text = " ".join(["word"] * 2000)
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i
