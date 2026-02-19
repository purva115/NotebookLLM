"""
LLM client + prompt templates for Gemini.
"""
import google.generativeai as genai
from app.core.config import GOOGLE_API_KEY, GEMINI_MODEL, MAX_OUTPUT_TOKENS, TEMPERATURE

genai.configure(api_key=GOOGLE_API_KEY)

_model = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    generation_config=genai.GenerationConfig(
        max_output_tokens=MAX_OUTPUT_TOKENS,
        temperature=TEMPERATURE,
    ),
)

# ── Prompt templates ──────────────────────────────────────────────────────────

RAG_SYSTEM_PROMPT = """You are a helpful AI assistant embedded in a research notebook.
Answer the user's question using ONLY the context provided below.
- Be concise and factual.
- Cite your sources using [1], [2], etc. corresponding to the context snippets.
- If the context does not contain enough information, say so honestly.
- Do NOT hallucinate information not present in the context."""

SUMMARY_PROMPT = """Summarize the following document in 3-5 concise bullet points.
Focus on the key ideas, findings, and important details.

Document:
{text}

Summary:"""

AUDIO_OVERVIEW_PROMPT = """You are writing a script for a short, engaging podcast episode (2-3 minutes).
Two hosts — Alex and Jamie — discuss the key insights from a research notebook.
Write it as a natural conversation with "Alex:" and "Jamie:" labels.

Notebook content summary:
{summary}

Podcast script:"""


# ── Generation helpers ────────────────────────────────────────────────────────

def generate_rag_answer(question: str, context: str, chat_history: list[dict]) -> str:
    """
    Generate a grounded answer given retrieved context and conversation history.

    Args:
        question:     The user's current question.
        context:      Retrieved context string (numbered chunks).
        chat_history: List of {role, content} dicts for the current session.

    Returns:
        The assistant's answer as a string.
    """
    prompt = f"{RAG_SYSTEM_PROMPT}\n\n--- Context ---\n{context}\n\n--- Question ---\n{question}"

    # Build Gemini conversation history
    history = []
    for msg in chat_history[-10:]:  # last 10 turns to stay within context window
        history.append({"role": msg["role"], "parts": [msg["content"]]})

    chat = _model.start_chat(history=history)
    response = chat.send_message(prompt)
    return response.text


def generate_text(prompt: str) -> str:
    """Simple one-shot text generation."""
    response = _model.generate_content(prompt)
    return response.text
