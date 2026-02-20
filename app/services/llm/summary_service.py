"""
summary_service.py — Generate per-source AI summaries and save report/quiz artifacts.
"""
from pathlib import Path

from app.services.llm.client import generate_text, SUMMARY_PROMPT
from app.services.storage import notebook_store


def generate_summary(text: str) -> str:
    """Return a bullet-point summary of the given text."""
    prompt = SUMMARY_PROMPT.format(text=text[:4000])  # cap at ~4000 chars
    return generate_text(prompt)


def save_report(username: str, notebook_id: str, md_text: str) -> Path:
    """Generate + persist a report artifact (.md). Returns the saved path."""
    return notebook_store.save_report(username, notebook_id, md_text)


def save_quiz(username: str, notebook_id: str, md_text: str) -> Path:
    """Generate + persist a quiz artifact (.md). Returns the saved path."""
    return notebook_store.save_quiz(username, notebook_id, md_text)
