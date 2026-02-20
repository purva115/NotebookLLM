

# NotebookLM Clone 📓

> An AI-powered research assistant inspired by Google NotebookLM.  
> Upload documents, chat with them using RAG, and generate study artifacts — all in isolated per-user notebooks.

---

## Features

| Feature | Details |
|---|---|
| 📄 **Source Ingestion** | PDF, PPTX, TXT, web URLs, YouTube transcripts |
| 💬 **RAG Chat** | Grounded answers with inline source citations |
| 📝 **Artifacts** | Auto-generate Reports, Quizzes, and Podcast audio |
| 🔒 **User Isolation** | Every user's data lives in their own directory |
| 📚 **Multi-Notebook** | Create, rename, and delete multiple notebooks per user |
| 💾 **Persistent Storage** | Files, chat history, and artifacts persist across sessions |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| UI | Gradio 4 | Native HF Spaces support, no JS/CSS needed |
| Auth | Hugging Face OAuth | No password database, seamless HF integration |
| LLM | Google Gemini 1.5 Pro | Long context window, free tier available |
| Embeddings | `text-embedding-004` | High quality, same API key as Gemini |
| Vector DB | ChromaDB (per-notebook) | File-based, no server needed, fully isolated |
| Metadata DB | SQLite + SQLAlchemy | Zero-infra, works on HF Spaces persistent disk |
| CI/CD | GitHub Actions | Auto-pushes to HF Space on every commit |

---

## Project Structure

```
NotebookLM/
├── app.py                          # Gradio app entry point (HF Spaces)
├── requirements.txt
├── .env.example                    # Copy to .env and fill in your keys
│
├── app/
│   ├── core/                       # Config, security helpers
│   ├── ui/                         # Gradio tab components (auth, notebooks, chat, sources)
│   ├── services/
│   │   ├── ingestion/              # PDF/PPTX/URL parser → chunker → embedder
│   │   ├── retrieval/              # Vector search + context builder
│   │   ├── llm/                    # Gemini client, RAG chat, summaries, audio
│   │   └── storage/
│   │       └── notebook_store.py   # All filesystem path logic (single source of truth)
│   └── db/                         # SQLite models + CRUD (notebooks, sources, chunks)
│
├── data/                           # Gitignored — created automatically at runtime
│   └── users/
│       └── <username>/
│           └── notebooks/
│               ├── index.json                  # List of all notebooks
│               └── <notebook-uuid>/
│                   ├── files_raw/              # Uploaded source files (PDF, PPTX, TXT)
│                   ├── files_extracted/        # Extracted plain text per source
│                   ├── chroma/                 # ChromaDB vector store (per notebook)
│                   ├── chat/
│                   │   └── messages.jsonl      # Chat history (one JSON object per line)
│                   └── artifacts/
│                       ├── reports/            # report_1.md, report_2.md, ...
│                       ├── quizzes/            # quiz_1.md, quiz_2.md, ...
│                       └── podcasts/           # podcast_1.mp3, podcast_2.mp3, ...
│
├── tests/
│   ├── unit/                       # Fast tests (no API keys needed)
│   └── integration/
└── docs/                           # Architecture docs and design brief
```

---

## Required Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|---|---|---|
| `GOOGLE_API_KEY` | Google AI Studio key (Gemini + Embeddings) | ✅ Yes |
| `SECRET_KEY` | Random 32-character string for session signing | ✅ Yes |
| `SQLITE_PATH` | Override SQLite DB path (default: `data/notebooklm.db`) | Optional |
| `DATA_DIR` | Override data root directory (default: `./data`) | Optional |

---

## Running Locally

```bash
# 1. Clone the repo
git clone https://github.com/purvas115/NotebookLLM.git
cd NotebookLLM

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — fill in GOOGLE_API_KEY and SECRET_KEY

# 4. Start the app
python app.py
# Visit http://localhost:7860
```

---

## Deploying to Hugging Face Spaces

1. Create a **Gradio** Space on [huggingface.co](https://huggingface.co/spaces).
2. Push this repo to the Space:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-org>/<your-space>
   git push space main
   ```
3. In **Space Settings → Secrets**, add `GOOGLE_API_KEY` and `SECRET_KEY`.
4. In **Space Settings → Storage**, attach a **Persistent Storage** volume mounted at `/data`.

> **Note:** On the free HF tier, `/data` is ephemeral — data resets if the Space rebuilds or sleeps after 48 hours of inactivity. This is fine for development. For production persistence, use a paid storage volume ($5/month).

---

## CI/CD (GitHub Actions)

A GitHub Actions workflow automatically syncs this repo to the HF Space on every push to `main`.

Add `HF_TOKEN` (a Hugging Face token with **write** access to your Space) as a GitHub repository secret under **Settings → Secrets and variables → Actions**.

---

## Running Tests

```bash
# Unit tests only (no API key required)
python -m pytest tests/unit/ -v

# All tests
python -m pytest -v
```

---

## Milestone Plan

| Milestone | Scope |
|---|---|
| **MVP** | HF OAuth + Notebook CRUD + PDF ingestion + RAG chat |
| **M2** | URL / YouTube ingestion, per-source AI summaries, artifact generation |
| **M3** | Podcast audio (TTS), persistent chat history, artifact downloads |
| **M4** | Additional file types, multi-speaker podcast, CI/CD, performance hardening |
