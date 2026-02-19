"""
summary_service.py — Generate per-source AI summaries.
"""
from app.services.llm.client import generate_text, SUMMARY_PROMPT


def generate_summary(text: str) -> str:
    """Return a bullet-point summary of the given text."""
    prompt = SUMMARY_PROMPT.format(text=text[:4000])  # cap at ~4000 chars
    return generate_text(prompt)
