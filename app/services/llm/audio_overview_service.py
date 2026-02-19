"""
audio_overview_service.py
Generates a podcast-style dialogue script from notebook summaries using Gemini.
"""
from app.services.llm.client import generate_text, AUDIO_OVERVIEW_PROMPT


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
