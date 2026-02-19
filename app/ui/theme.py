"""
Gradio custom theme for NotebookLM Clone.
"""
import gradio as gr


def notebooklm_theme() -> gr.Theme:
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="indigo",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
    ).set(
        body_background_fill="#0f172a",
        body_background_fill_dark="#0f172a",
        block_background_fill="#1e293b",
        block_background_fill_dark="#1e293b",
        block_border_color="#334155",
        block_label_text_color="#94a3b8",
        input_background_fill="#0f172a",
        input_border_color="#334155",
        button_primary_background_fill="#3b82f6",
        button_primary_background_fill_hover="#2563eb",
        button_secondary_background_fill="#1e293b",
        button_secondary_border_color="#334155",
    )
