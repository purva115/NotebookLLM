"""
sources_tab.py — Upload and manage sources for the active notebook.
Supports PDF, DOCX, plain text uploads and URL / YouTube links.
"""
import os
import shutil
import threading
import gradio as gr

from app.core.config import UPLOAD_DIR
from app.db.session import get_db
from app.db import crud
from app.services.ingestion.pipeline import ingest_file


def build_sources_tab(session_state: gr.State):

    with gr.Column():
        gr.Markdown("## 📄 Sources")
        gr.Markdown("*Add documents or links to your active notebook. Ingestion runs in the background.*")

        with gr.Tabs():
            with gr.Tab("📁 Upload File"):
                file_upload = gr.File(
                    label="Upload PDF, DOCX, or TXT",
                    file_types=[".pdf", ".docx", ".txt"],
                )
                upload_btn = gr.Button("⬆️ Add File Source", variant="primary")

            with gr.Tab("🌐 URL / YouTube"):
                url_input = gr.Textbox(label="Paste a URL or YouTube link", placeholder="https://...")
                url_btn = gr.Button("➕ Add URL Source", variant="primary")

        source_status = gr.Markdown("")

        gr.Markdown("### 📋 Sources in this Notebook")
        sources_display = gr.Dataframe(
            headers=["Title", "Type", "Status", "Summary Preview"],
            datatype=["str", "str", "str", "str"],
            interactive=False,
        )

        with gr.Row():
            refresh_sources_btn = gr.Button("🔄 Refresh Sources")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _run_ingestion_background(notebook_id, source_id, file_path, source_type, url=None):
        """Fire-and-forget ingestion in a daemon thread."""
        def _run():
            try:
                ingest_file(notebook_id, source_id, file_path, source_type, url=url)
            except Exception as e:
                print(f"[Ingestion Error] source={source_id}: {e}")
        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def _sources_table(notebook_id):
        with get_db() as db:
            sources = crud.get_sources(db, notebook_id)
        rows = []
        for s in sources:
            preview = (s.summary or "")[:80] + ("…" if s.summary and len(s.summary) > 80 else "")
            rows.append([s.title, s.source_type, s.status, preview])
        return rows

    # ── Upload file ───────────────────────────────────────────────────────────

    def add_file_source(file, state):
        if not state.get("user_id"):
            return state, "⚠️ Please sign in first.", []
        if not state.get("notebook_id"):
            return state, "⚠️ Please select a notebook first.", []
        if file is None:
            return state, "⚠️ No file selected.", []

        src_path = file.name
        filename = os.path.basename(src_path)
        ext = filename.rsplit(".", 1)[-1].lower()
        source_type = {"pdf": "pdf", "docx": "docx", "txt": "text"}.get(ext, "text")

        # Copy to persistent UPLOAD_DIR
        dest = UPLOAD_DIR / filename
        shutil.copy(src_path, dest)

        with get_db() as db:
            src = crud.create_source(db, state["notebook_id"], title=filename,
                                     source_type=source_type, file_path=str(dest))

        _run_ingestion_background(state["notebook_id"], src.id, str(dest), source_type)
        rows = _sources_table(state["notebook_id"])
        return state, f"⏳ Ingesting **{filename}** — status will update when ready.", rows

    # ── URL / YouTube ─────────────────────────────────────────────────────────

    def add_url_source(url, state):
        if not state.get("user_id"):
            return state, "⚠️ Please sign in first.", []
        if not state.get("notebook_id"):
            return state, "⚠️ Please select a notebook first.", []
        if not url.strip():
            return state, "⚠️ Please enter a URL.", []

        source_type = "youtube" if "youtube.com" in url or "youtu.be" in url else "url"
        title = url[:80]

        with get_db() as db:
            src = crud.create_source(db, state["notebook_id"], title=title,
                                     source_type=source_type, original_url=url.strip())

        _run_ingestion_background(state["notebook_id"], src.id, None, source_type, url=url.strip())
        rows = _sources_table(state["notebook_id"])
        return state, f"⏳ Ingesting **{title}**…", rows

    def refresh_sources(state):
        if not state.get("notebook_id"):
            return "⚠️ No notebook selected.", []
        rows = _sources_table(state["notebook_id"])
        return "", rows

    upload_btn.click(add_file_source, inputs=[file_upload, session_state],
                     outputs=[session_state, source_status, sources_display])
    url_btn.click(add_url_source, inputs=[url_input, session_state],
                  outputs=[session_state, source_status, sources_display])
    refresh_sources_btn.click(refresh_sources, inputs=[session_state],
                              outputs=[source_status, sources_display])
