"""
pipeline.py
Full ingestion pipeline: parse → chunk → embed → store per the spec tree.

Storage layout produced per source:
  files_raw/<source_id>_<filename>       ← raw uploaded bytes
  files_extracted/<source_id>.txt        ← plain extracted text
  chroma/                                ← ChromaDB (notebook-scoped)
"""
import shutil
from pathlib import Path
from typing import Optional

from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.db.session import get_db
from app.db import crud
from app.services.ingestion.document_parser import parse_document
from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.embedder import embed_texts
from app.services.llm.summary_service import generate_summary
from app.services.storage import notebook_store


def ingest_file(
    username: str,
    notebook_id: str,
    source_id: str,
    file_path: str,
    source_type: str,
    url: Optional[str] = None,
) -> None:
    """
    Run the complete ingestion pipeline for one source.

    Steps:
      1. Copy raw file into files_raw/
      2. Parse → plain text, save to files_extracted/
      3. Chunk text
      4. Embed chunks via Gemini
      5. Upsert embeddings into per-notebook ChromaDB
      6. Save chunk metadata to SQLite
      7. Generate per-source AI summary
      8. Update source status to "ready"
    """
    with get_db() as db:
        try:
            crud.update_source_status(db, source_id, "processing")

            # 1. Copy raw file → files_raw/
            src_path = Path(file_path) if file_path else None
            raw_dir = notebook_store.get_files_raw_dir(username, notebook_id)
            if src_path and src_path.exists():
                dest_raw = raw_dir / f"{source_id}_{src_path.name}"
                shutil.copy2(src_path, dest_raw)
                file_bytes = dest_raw.read_bytes()
            else:
                file_bytes = None

            # 2. Parse → plain text
            text = parse_document(source_type, file_bytes=file_bytes, url=url)

            # Save extracted text → files_extracted/<source_id>.txt
            extracted_dir = notebook_store.get_files_extracted_dir(username, notebook_id)
            (extracted_dir / f"{source_id}.txt").write_text(text, encoding="utf-8")

            # 3. Chunk
            raw_chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

            # 4. Embed
            contents = [c["content"] for c in raw_chunks]
            vectors = embed_texts(contents)

            # 5. Save chunks to SQLite and collect IDs
            db_chunks = crud.create_chunks(db, source_id, raw_chunks)

            # 6. Upsert into per-notebook ChromaDB
            collection = notebook_store.get_chroma_collection(username, notebook_id)
            collection.upsert(
                ids=[c.id for c in db_chunks],
                embeddings=vectors,
                documents=contents,
                metadatas=[
                    {"source_id": source_id, "chunk_index": c.chunk_index}
                    for c in db_chunks
                ],
            )

            # 7. Summary
            summary_text = " ".join(text.split()[:3000])
            summary = generate_summary(summary_text)

            # 8. Mark ready
            crud.update_source_status(db, source_id, "ready", summary=summary)

        except Exception as e:
            crud.update_source_status(db, source_id, "failed")
            raise e


def delete_source_data(
    username: str,
    notebook_id: str,
    source_id: str,
    chunk_ids: list[str],
) -> None:
    """Remove chunk embeddings from ChromaDB and extracted text when a source is deleted."""
    if chunk_ids:
        collection = notebook_store.get_chroma_collection(username, notebook_id)
        collection.delete(ids=chunk_ids)

    # Remove extracted text file if present
    extracted = (
        notebook_store.get_files_extracted_dir(username, notebook_id)
        / f"{source_id}.txt"
    )
    if extracted.exists():
        extracted.unlink()
