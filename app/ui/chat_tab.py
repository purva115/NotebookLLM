"""
chat_tab.py — RAG-powered chat Gradio tab.
"""
import gradio as gr

from app.services.llm.chat_service import chat as rag_chat
from app.services.llm.audio_overview_service import generate_audio_overview
from app.db.session import get_db
from app.db import crud


def build_chat_tab(session_state: gr.State):

    with gr.Column():
        gr.Markdown("## 💬 Chat with your Notebook")
        gr.Markdown("*Ask questions — answers are grounded in your uploaded sources.*")

        chatbot = gr.Chatbot(
            label="Notebook Chat",
            height=450,
            bubble_full_width=False,
            show_copy_button=True,
        )

        with gr.Row():
            user_input = gr.Textbox(
                placeholder="Ask anything about your sources…",
                label="",
                scale=5,
                lines=1,
                autofocus=True,
            )
            send_btn = gr.Button("Send ➤", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("🧹 Clear Chat")
            history_btn = gr.Button("📜 Load History")
            audio_btn = gr.Button("🎙️ Generate Audio Overview")

        chat_status = gr.Markdown("")
        audio_output = gr.Audio(label="Audio Overview", visible=False)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def send_message(user_msg: str, history: list, state: dict):
        if not state.get("user_id"):
            history.append((user_msg, "⚠️ Please sign in first."))
            return "", history, state
        if not state.get("notebook_id"):
            history.append((user_msg, "⚠️ Please select a notebook first."))
            return "", history, state
        if not user_msg.strip():
            return "", history, state

        answer, cited_ids = rag_chat(state["notebook_id"], user_msg, history)

        # Append citation note if we got some
        if cited_ids:
            answer += f"\n\n*— Based on {len(cited_ids)} source chunk(s)*"

        history.append((user_msg, answer))
        return "", history, state

    def load_history(state: dict):
        if not state.get("notebook_id"):
            return [], "⚠️ No notebook selected."
        with get_db() as db:
            messages = crud.get_chat_history(db, state["notebook_id"])
        history = []
        for msg in messages:
            if msg.role == "user":
                history.append((msg.content, None))
            else:
                if history and history[-1][1] is None:
                    history[-1] = (history[-1][0], msg.content)
                else:
                    history.append((None, msg.content))
        return history, ""

    def clear_chat():
        return [], ""

    def make_audio_overview(state: dict):
        if not state.get("notebook_id"):
            return gr.update(visible=False), "⚠️ No notebook selected."
        with get_db() as db:
            sources = crud.get_sources(db, state["notebook_id"])
        summaries = [s.summary for s in sources if s.summary]
        if not summaries:
            return gr.update(visible=False), "⚠️ No source summaries yet. Add and process sources first."
        combined = "\n\n".join(summaries)
        script = generate_audio_overview(combined)
        # Return script as text (full TTS would need additional integration)
        return gr.update(visible=False), f"**🎙️ Audio Overview Script:**\n\n{script}"

    send_btn.click(send_message, inputs=[user_input, chatbot, session_state],
                   outputs=[user_input, chatbot, session_state])
    user_input.submit(send_message, inputs=[user_input, chatbot, session_state],
                      outputs=[user_input, chatbot, session_state])
    clear_btn.click(clear_chat, outputs=[chatbot, chat_status])
    history_btn.click(load_history, inputs=[session_state], outputs=[chatbot, chat_status])
    audio_btn.click(make_audio_overview, inputs=[session_state],
                    outputs=[audio_output, chat_status])
