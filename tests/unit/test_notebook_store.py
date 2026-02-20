"""
test_notebook_store.py
Unit tests for app/services/storage/notebook_store.py
All tests use a temporary directory so they never touch the real /data folder.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# ── Patch USERS_DIR before importing notebook_store ──────────────────────────
@pytest.fixture(autouse=True)
def temp_users_dir(tmp_path, monkeypatch):
    """Redirect USERS_DIR to a throwaway temp directory for every test."""
    import app.core.config as cfg
    monkeypatch.setattr(cfg, "USERS_DIR", tmp_path / "users")
    (tmp_path / "users").mkdir(parents=True, exist_ok=True)

    # Re-import so notebook_store picks up the patched value
    import importlib
    import app.services.storage.notebook_store as ns
    importlib.reload(ns)
    return tmp_path


USERNAME = "test_user"
NB_ID = "notebook-1234"


# ── Path helpers ──────────────────────────────────────────────────────────────

def test_notebook_dir_created(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p = ns.get_notebook_dir(USERNAME, NB_ID)
    assert p.is_dir()


def test_files_raw_dir_created(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p = ns.get_files_raw_dir(USERNAME, NB_ID)
    assert p.is_dir()
    assert p.name == "files_raw"


def test_files_extracted_dir_created(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p = ns.get_files_extracted_dir(USERNAME, NB_ID)
    assert p.is_dir()
    assert p.name == "files_extracted"


def test_chroma_dir_created(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p = ns.get_chroma_dir(USERNAME, NB_ID)
    assert p.is_dir()
    assert p.name == "chroma"


def test_artifacts_dir_created(temp_users_dir):
    from app.services.storage import notebook_store as ns
    for kind in ("reports", "quizzes", "podcasts"):
        p = ns.get_artifacts_dir(USERNAME, NB_ID, kind)
        assert p.is_dir()
        assert p.name == kind


def test_artifacts_dir_invalid_kind(temp_users_dir):
    from app.services.storage import notebook_store as ns
    with pytest.raises(ValueError):
        ns.get_artifacts_dir(USERNAME, NB_ID, "invalid")


# ── Chat history (messages.jsonl) ─────────────────────────────────────────────

def test_empty_chat_history(temp_users_dir):
    from app.services.storage import notebook_store as ns
    history = ns.read_chat_history(USERNAME, NB_ID)
    assert history == []


def test_append_and_read_chat_messages(temp_users_dir):
    from app.services.storage import notebook_store as ns

    ns.append_chat_message(USERNAME, NB_ID, "user", "Hello!")
    ns.append_chat_message(USERNAME, NB_ID, "assistant", "Hi there!", cited_ids=["c1", "c2"])

    history = ns.read_chat_history(USERNAME, NB_ID)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello!"
    assert history[1]["role"] == "assistant"
    assert history[1]["cited_ids"] == ["c1", "c2"]


def test_messages_jsonl_is_one_json_per_line(temp_users_dir):
    from app.services.storage import notebook_store as ns

    ns.append_chat_message(USERNAME, NB_ID, "user", "Test")
    path = ns.get_messages_jsonl(USERNAME, NB_ID)
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["content"] == "Test"


# ── Artifact save helpers ─────────────────────────────────────────────────────

def test_save_report(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p = ns.save_report(USERNAME, NB_ID, "# My Report\n\nContent here.")
    assert p.exists()
    assert p.name == "report_1.md"
    assert "My Report" in p.read_text(encoding="utf-8")


def test_save_report_auto_increments(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p1 = ns.save_report(USERNAME, NB_ID, "Report 1")
    p2 = ns.save_report(USERNAME, NB_ID, "Report 2")
    assert p1.name == "report_1.md"
    assert p2.name == "report_2.md"


def test_save_quiz(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p = ns.save_quiz(USERNAME, NB_ID, "## Quiz\n\n1. Q?")
    assert p.exists()
    assert p.name == "quiz_1.md"


def test_save_podcast(temp_users_dir):
    from app.services.storage import notebook_store as ns
    p = ns.save_podcast(USERNAME, NB_ID, b"\xff\xfb\x90\x00" * 10)  # fake mp3 bytes
    assert p.exists()
    assert p.name == "podcast_1.mp3"
    assert p.read_bytes() == b"\xff\xfb\x90\x00" * 10


# ── Notebook index ────────────────────────────────────────────────────────────

def test_notebook_index_roundtrip(temp_users_dir):
    from app.services.storage import notebook_store as ns
    entries = [{"id": "abc", "title": "Test NB", "created_at": "2026-01-01"}]
    ns.save_notebook_index(USERNAME, entries)
    loaded = ns.load_notebook_index(USERNAME)
    assert loaded == entries


def test_notebook_index_empty_when_missing(temp_users_dir):
    from app.services.storage import notebook_store as ns
    assert ns.load_notebook_index("nonexistent_user") == []
