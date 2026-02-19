---
title: NotebookLM Clone
emoji: 📓
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "4.31.5"
app_file: app.py
pinned: false
license: mit
---

# NotebookLM Clone 📓

An AI-powered notebook application inspired by Google NotebookLM.  
Upload PDFs, paste URLs or YouTube links, then ask any question — grounded answers with inline citations.

## Features
- 📄 Multi-source ingestion: PDF, URL, YouTube transcripts, plain text
- 🤖 RAG-powered chat with Gemini (grounded answers + citations)
- 📝 Per-source AI summaries
- 🎙️ Audio Overview (podcast-style dialogue)
- 🔒 Per-user data isolation via session tokens
- 💾 SQLite + ChromaDB (zero-infra, HF Spaces compatible)

## Tech Stack
| Layer | Choice | Reason |
|---|---|---|
| UI | Gradio 4 | Native HF Spaces support, minimal boilerplate |
| LLM | Google Gemini 1.5 Pro | Long context, free tier available |
| Embeddings | `text-embedding-004` | High quality, same API key |
| Vector DB | ChromaDB (persistent) | File-based, no server needed |
| Relational DB | SQLite + SQLAlchemy | Zero-infra, HF Spaces persistent disk |
| File storage | Local `/data/uploads` | HF Spaces persistent storage volume |
| Auth | bcrypt + session tokens | Simple, stateless, no OAuth dependency |

## Setup

### Run locally
```bash
git clone <repo>
cd NotebookLM
pip install -r requirements.txt
cp .env.example .env   # fill in GOOGLE_API_KEY
python app.py
```

### Deploy to HF Spaces
1. Push this repo to a HF Space (Gradio SDK)
2. Go to **Settings → Secrets** and add:
   - `GOOGLE_API_KEY`
   - `SECRET_KEY` (random 32-char string)
3. HF will auto-run `app.py`

## Project Structure
```
NotebookLM/
├── app.py                  # HF Spaces entry point (Gradio app)
├── requirements.txt
├── .env.example
├── app/
│   ├── ui/                 # Gradio tab components
│   │   ├── auth_tab.py
│   │   ├── notebook_tab.py
│   │   ├── sources_tab.py
│   │   ├── chat_tab.py
│   │   └── theme.py
│   ├── core/               # Config, security, auth logic
│   ├── services/
│   │   ├── ingestion/      # Parse → chunk → embed → store
│   │   ├── retrieval/      # Vector search + context builder
│   │   ├── llm/            # Gemini client, prompts, chat/summary/audio
│   │   └── storage/        # File I/O helpers
│   ├── db/                 # SQLAlchemy + SQLite models, CRUD, init
│   └── utils/
├── data/
│   ├── uploads/            # Uploaded files (gitignored)
│   └── chroma/             # ChromaDB persistent store (gitignored)
├── tests/
└── docs/
```

## Milestone Plan
| # | Milestone | Scope |
|---|---|---|
| MVP | Auth + Notebook CRUD + PDF ingestion + RAG chat | Core loop working |
| M2 | URL / YouTube sources + per-source summaries | Richer sources |
| M3 | Audio Overview generation + note editor | Power features |
| M4 | Multi-language, export, performance hardening | Polish |
