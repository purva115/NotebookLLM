"""
audio_overview_service.py
Generates a podcast-style dialogue script from notebook summaries using Gemini,
then saves the audio to the spec-defined artifacts/podcasts/ directory.
"""
from pathlib import Path
from typing import Optional

from app.services.llm.client import generate_text, AUDIO_OVERVIEW_PROMPT
from app.services.storage import notebook_store


def generate_audio_overview(combined_summary: str) -> str:
    """
    Generate a short Alex-&-Jamie podcast script from source summaries.

    Args:
        combined_summary: Concatenated per-source summaries.

    Returns:
        A formatted podcast dialogue script string.
    """
    prompt = AUDIO_OVERVIEW_PROMPT.format(summary=combined_summary[:3000])
    return generate_text(prompt)


def save_podcast(username: str, notebook_id: str, mp3_bytes: bytes) -> Path:
    """
    Persist a generated podcast audio file (.mp3) to the spec-defined
    artifacts/podcasts/ directory.

    Args:
        username:    HF username (used for filesystem isolation).
        notebook_id: Notebook UUID.
        mp3_bytes:   Raw MP3 audio bytes.

    Returns:
        Path to the saved .mp3 file.
    """
    return notebook_store.save_podcast(username, notebook_id, mp3_bytes)
