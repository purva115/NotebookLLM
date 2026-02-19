"""
pipeline.py
Full ingestion pipeline: parse → chunk → embed → store in ChromaDB + SQLite.
"""
import os
import shutil
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import UPLOAD_DIR, CHROMA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from app.db.session import get_db
from app.db import crud
from app.services.ingestion.document_parser import parse_document
from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.embedder import embed_texts
from app.services.llm.summary_service import generate_summary

# Initialise ChromaDB persistent client (file-based — no server needed)
_chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),
    settings=ChromaSettings(anonymized_telemetry=False),
)


def _get_chroma_collection(notebook_id: str):
    """Each notebook gets its own ChromaDB collection for data isolation."""
    return _chroma_client.get_or_create_collection(
        name=f"notebook_{notebook_id}",
        metadata={"hnsw:space": "cosine"},
    )


def ingest_file(
    notebook_id: str,
    source_id: str,
    file_path: str,
    source_type: str,
    url: Optional[str] = None,
) -> None:
    """
    Run the complete ingestion pipeline for one source.

    Steps:
      1. Read file bytes (or use URL)
      2. Parse → plain text
      3. Chunk text
      4. Embed chunks via Gemini
      5. Upsert embeddings into ChromaDB (notebook-scoped collection)
      6. Save chunk metadata to SQLite
      7. Generate per-source AI summary
      8. Update source status to "ready"
    """
    with get_db() as db:
        try:
            # Mark processing
            crud.update_source_status(db, source_id, "processing")

            # 1. Read bytes if file-based
            file_bytes = None
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_bytes = f.read()

            # 2. Parse
            text = parse_document(source_type, file_bytes=file_bytes, url=url)

            # 3. Chunk
            raw_chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

            # 4. Embed
            contents = [c["content"] for c in raw_chunks]
            vectors = embed_texts(contents)

            # 5. Save chunks to SQLite and collect IDs
            db_chunks = crud.create_chunks(db, source_id, raw_chunks)

            # 6. Upsert into ChromaDB
            collection = _get_chroma_collection(notebook_id)
            collection.upsert(
                ids=[c.id for c in db_chunks],
                embeddings=vectors,
                documents=contents,
                metadatas=[{"source_id": source_id, "chunk_index": c.chunk_index} for c in db_chunks],
            )

            # 7. Summary (first 3000 words of text to keep prompt small)
            summary_text = " ".join(text.split()[:3000])
            summary = generate_summary(summary_text)

            # 8. Mark ready
            crud.update_source_status(db, source_id, "ready", summary=summary)

        except Exception as e:
            crud.update_source_status(db, source_id, "failed")
            raise e


def delete_source_data(notebook_id: str, source_id: str, chunk_ids: list[str]) -> None:
    """Remove chunk embeddings from ChromaDB when a source is deleted."""
    if chunk_ids:
        collection = _get_chroma_collection(notebook_id)
        collection.delete(ids=chunk_ids)
