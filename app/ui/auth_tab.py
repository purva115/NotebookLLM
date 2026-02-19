"""
auth_tab.py — Sign In / Register Gradio tab.
"""
import gradio as gr

from app.db.session import get_db
from app.db import crud
from app.core.security import create_session_token, verify_session_token


def build_auth_tab(session_state: gr.State):
    """Render the auth tab and wire up login/register logic."""

    with gr.Column():
        gr.Markdown("## 🔐 Sign In or Create Account")

        with gr.Tab("Sign In"):
            login_email = gr.Textbox(label="Email", placeholder="you@example.com")
            login_password = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Sign In", variant="primary")
            login_status = gr.Markdown("")

        with gr.Tab("Register"):
            reg_name = gr.Textbox(label="Full Name", placeholder="Jane Doe")
            reg_email = gr.Textbox(label="Email", placeholder="you@example.com")
            reg_password = gr.Textbox(label="Password", type="password")
            reg_btn = gr.Button("Create Account", variant="primary")
            reg_status = gr.Markdown("")

    # ── Handlers ──────────────────────────────────────────────────────────────

    def do_login(email: str, password: str, state: dict):
        with get_db() as db:
            user = crud.authenticate_user(db, email.strip(), password)
        if not user:
            return state, "❌ Invalid email or password."
        token = create_session_token(user.id)
        state["user_id"] = user.id
        state["token"] = token
        state["notebook_id"] = None
        return state, f"✅ Welcome back, **{user.full_name or user.email}**!"

    def do_register(name: str, email: str, password: str, state: dict):
        if not email.strip() or not password.strip():
            return state, "❌ Email and password are required."
        with get_db() as db:
            existing = crud.get_user_by_email(db, email.strip())
            if existing:
                return state, "❌ An account with this email already exists."
            user = crud.create_user(db, email.strip(), password, full_name=name.strip() or None)
        token = create_session_token(user.id)
        state["user_id"] = user.id
        state["token"] = token
        state["notebook_id"] = None
        return state, f"✅ Account created! Welcome, **{name or email}**."

    login_btn.click(
        do_login,
        inputs=[login_email, login_password, session_state],
        outputs=[session_state, login_status],
    )
    reg_btn.click(
        do_register,
        inputs=[reg_name, reg_email, reg_password, session_state],
        outputs=[session_state, reg_status],
    )
