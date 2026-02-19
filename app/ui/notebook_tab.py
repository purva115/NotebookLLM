"""
notebook_tab.py — My Notebooks Gradio tab.
Create, select, rename, and delete notebooks.
"""
import gradio as gr

from app.db.session import get_db
from app.db import crud


def build_notebook_tab(session_state: gr.State):

    with gr.Column():
        gr.Markdown("## 📚 My Notebooks")

        with gr.Row():
            new_title = gr.Textbox(label="New Notebook Title", placeholder="e.g. My Research Notes", scale=4)
            create_btn = gr.Button("＋ Create", variant="primary", scale=1)

        notebook_status = gr.Markdown("")

        notebook_list = gr.Radio(
            choices=[],
            label="Select a notebook to work in",
            interactive=True,
        )

        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh")
            delete_btn = gr.Button("🗑️ Delete Selected", variant="stop")

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _notebook_choices(user_id: str):
        with get_db() as db:
            notebooks = crud.get_notebooks(db, user_id)
        return [(f"{nb.title}", nb.id) for nb in notebooks]

    def refresh_notebooks(state: dict):
        if not state.get("user_id"):
            return gr.update(choices=[]), "⚠️ Please sign in first."
        choices = _notebook_choices(state["user_id"])
        return gr.update(choices=choices, value=None), ""

    def create_notebook(title: str, state: dict):
        if not state.get("user_id"):
            return state, gr.update(choices=[]), "⚠️ Please sign in first."
        with get_db() as db:
            nb = crud.create_notebook(db, state["user_id"], title=title.strip() or "Untitled Notebook")
        choices = _notebook_choices(state["user_id"])
        return state, gr.update(choices=choices, value=nb.id), f"✅ Created **{nb.title}**"

    def select_notebook(selected_id: str, state: dict):
        state["notebook_id"] = selected_id
        return state, f"📓 Active notebook: `{selected_id}`"

    def delete_notebook(state: dict):
        nb_id = state.get("notebook_id")
        if not nb_id:
            return state, gr.update(), "⚠️ No notebook selected."
        with get_db() as db:
            crud.delete_notebook(db, nb_id, state["user_id"])
        state["notebook_id"] = None
        choices = _notebook_choices(state["user_id"])
        return state, gr.update(choices=choices, value=None), "🗑️ Notebook deleted."

    refresh_btn.click(refresh_notebooks, inputs=[session_state], outputs=[notebook_list, notebook_status])
    create_btn.click(create_notebook, inputs=[new_title, session_state], outputs=[session_state, notebook_list, notebook_status])
    notebook_list.change(select_notebook, inputs=[notebook_list, session_state], outputs=[session_state, notebook_status])
    delete_btn.click(delete_notebook, inputs=[session_state], outputs=[session_state, notebook_list, notebook_status])
