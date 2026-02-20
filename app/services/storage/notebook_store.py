"""
notebook_store.py
-----------------
Single source of truth for ALL filesystem paths in the spec-defined storage tree:

/data/
└── users/
    └── <username>/
        └── notebooks/
            ├── index.json
            └── <notebook-uuid>/
                ├── files_raw/
                ├── files_extracted/
                ├── chroma/
                ├── chat/
                │   └── messages.jsonl
                └── artifacts/
                    ├── reports/
                    ├── quizzes/
                    └── podcasts/

All functions are pure helpers – they create directories on demand and
never touch SQLite.  Storage-layer callers (pipeline, vector_search,
chat_service, artifact services) import from here.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import USERS_DIR


# ── Internal path builder ─────────────────────────────────────────────────────

def _notebooks_root(username: str) -> Path:
    """…/data/users/<username>/notebooks/"""
    p = USERS_DIR / _safe(username) / "notebooks"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe(name: str) -> str:
    """Strip characters that are unsafe as directory names."""
    return re.sub(r"[^\w\-.]", "_", name)


# ── Public path helpers ───────────────────────────────────────────────────────

def get_notebook_dir(username: str, notebook_id: str) -> Path:
    """Root directory for a single notebook."""
    p = _notebooks_root(username) / notebook_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_files_raw_dir(username: str, notebook_id: str) -> Path:
    p = get_notebook_dir(username, notebook_id) / "files_raw"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_files_extracted_dir(username: str, notebook_id: str) -> Path:
    p = get_notebook_dir(username, notebook_id) / "files_extracted"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_chroma_dir(username: str, notebook_id: str) -> Path:
    p = get_notebook_dir(username, notebook_id) / "chroma"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_chat_dir(username: str, notebook_id: str) -> Path:
    p = get_notebook_dir(username, notebook_id) / "chat"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_messages_jsonl(username: str, notebook_id: str) -> Path:
    return get_chat_dir(username, notebook_id) / "messages.jsonl"


def get_artifacts_dir(username: str, notebook_id: str, kind: str) -> Path:
    """
    kind must be one of: 'reports', 'quizzes', 'podcasts'
    """
    valid = {"reports", "quizzes", "podcasts"}
    if kind not in valid:
        raise ValueError(f"artifact kind must be one of {valid}, got {kind!r}")
    p = get_notebook_dir(username, notebook_id) / "artifacts" / kind
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_index_json(username: str) -> Path:
    """Path to the per-user notebooks/index.json."""
    return _notebooks_root(username) / "index.json"


# ── ChromaDB helper ───────────────────────────────────────────────────────────

def get_chroma_client(username: str, notebook_id: str) -> chromadb.PersistentClient:
    """Return a ChromaDB PersistentClient scoped to this notebook's chroma/ dir."""
    return chromadb.PersistentClient(
        path=str(get_chroma_dir(username, notebook_id)),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_chroma_collection(username: str, notebook_id: str):
    """Return (or create) the single ChromaDB collection for this notebook."""
    client = get_chroma_client(username, notebook_id)
    return client.get_or_create_collection(
        name="sources",
        metadata={"hnsw:space": "cosine"},
    )


# ── Chat history (messages.jsonl) ─────────────────────────────────────────────

def append_chat_message(
    username: str,
    notebook_id: str,
    role: str,
    content: str,
    cited_ids: Optional[List[str]] = None,
) -> None:
    """Append one message as a JSON line to messages.jsonl."""
    record = {
        "role": role,
        "content": content,
        "cited_ids": cited_ids or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    path = get_messages_jsonl(username, notebook_id)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_chat_history(username: str, notebook_id: str) -> List[dict]:
    """Read all messages from messages.jsonl; returns [] if file absent."""
    path = get_messages_jsonl(username, notebook_id)
    if not path.exists():
        return []
    messages = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return messages


# ── Artifact save helpers ─────────────────────────────────────────────────────

def _next_artifact_path(username: str, notebook_id: str, kind: str, ext: str) -> Path:
    """Auto-number artifacts: report_1.md, report_2.md, …"""
    prefix_map = {"reports": "report", "quizzes": "quiz", "podcasts": "podcast"}
    prefix = prefix_map[kind]
    d = get_artifacts_dir(username, notebook_id, kind)
    existing = sorted(d.glob(f"{prefix}_*.{ext}"))
    n = len(existing) + 1
    return d / f"{prefix}_{n}.{ext}"


def save_report(username: str, notebook_id: str, md_text: str) -> Path:
    """Save a generated report (.md) and return its path."""
    path = _next_artifact_path(username, notebook_id, "reports", "md")
    path.write_text(md_text, encoding="utf-8")
    return path


def save_quiz(username: str, notebook_id: str, md_text: str) -> Path:
    """Save a generated quiz (.md) and return its path."""
    path = _next_artifact_path(username, notebook_id, "quizzes", "md")
    path.write_text(md_text, encoding="utf-8")
    return path


def save_podcast(username: str, notebook_id: str, mp3_bytes: bytes) -> Path:
    """Save a generated podcast (.mp3) and return its path."""
    path = _next_artifact_path(username, notebook_id, "podcasts", "mp3")
    path.write_bytes(mp3_bytes)
    return path


# ── Notebook index (index.json) ───────────────────────────────────────────────

def load_notebook_index(username: str) -> List[dict]:
    """Load the list of notebook metadata dicts from index.json."""
    path = get_index_json(username)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_notebook_index(username: str, entries: List[dict]) -> None:
    """Persist the notebook index to index.json."""
    path = get_index_json(username)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
