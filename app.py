"""
app.py — HuggingFace Spaces entry point
========================================
Builds the Gradio app and launches it.
HF Spaces automatically runs this file.
"""
import gradio as gr

from app.db.init_db import init_db
from app.ui.theme import notebooklm_theme
from app.ui.auth_tab import build_auth_tab
from app.ui.notebook_tab import build_notebook_tab
from app.ui.sources_tab import build_sources_tab
from app.ui.chat_tab import build_chat_tab

# ── Bootstrap ─────────────────────────────────────────────────────────────────
init_db()  # Create SQLite tables if they don't exist

# ── Build Gradio app ──────────────────────────────────────────────────────────
with gr.Blocks(
    theme=notebooklm_theme(),
    title="NotebookLM Clone",
    css="""
    .tab-nav button { font-size: 15px; font-weight: 600; }
    .source-card { border: 1px solid #374151; border-radius: 8px; padding: 12px; margin: 6px 0; }
    .chat-bubble-user { background: #1e3a5f; border-radius: 12px; padding: 10px 14px; }
    .chat-bubble-ai   { background: #1a1a2e; border-radius: 12px; padding: 10px 14px; }
    """,
) as demo:

    # Shared session state (user_id stored after login)
    session_state = gr.State({"user_id": None, "notebook_id": None})

    gr.Markdown(
        """
        # 📓 NotebookLM Clone
        *AI-powered Q&A grounded in your documents — powered by Gemini*
        """
    )

    with gr.Tabs():
        with gr.Tab("🔐 Sign In / Register"):
            build_auth_tab(session_state)

        with gr.Tab("📚 My Notebooks"):
            build_notebook_tab(session_state)

        with gr.Tab("📄 Sources"):
            build_sources_tab(session_state)

        with gr.Tab("💬 Chat"):
            build_chat_tab(session_state)


# ── Launch ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",   # required for HF Spaces
        server_port=7860,         # HF Spaces default port
        share=False,
    )
