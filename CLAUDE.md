# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the server (from repo root)
./run.sh

# Or manually
cd backend && uv run uvicorn app:app --reload --port 8000
```

The app serves on `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Architecture

This is a full-stack RAG chatbot: a **FastAPI backend** serving both the API and a static vanilla JS frontend.

### Request flow

1. Frontend (`frontend/script.js`) POSTs `{ query, session_id }` to `/api/query`
2. `backend/app.py` routes to `RAGSystem.query()`
3. `RAGSystem` fetches conversation history from `SessionManager`, then calls `AIGenerator`
4. `AIGenerator` makes a **first Claude API call** with the `search_course_content` tool available
5. If Claude invokes the tool, `VectorStore.search()` runs a semantic search against ChromaDB and returns the top chunks
6. A **second Claude API call** synthesizes the chunks into a final answer
7. Sources and answer are returned to the frontend and rendered as Markdown

### Key components

- **`backend/rag_system.py`** — Main orchestrator. Wires together all components. Entry point for query handling.
- **`backend/ai_generator.py`** — Wraps the Anthropic SDK. Handles the two-turn tool-use loop (call → tool execution → follow-up call). Uses `claude-sonnet-4-20250514`, temp=0, max_tokens=800.
- **`backend/vector_store.py`** — ChromaDB wrapper with two collections: `course_catalog` (course-level metadata for fuzzy name resolution) and `course_content` (chunked text for semantic search). Uses `all-MiniLM-L6-v2` embeddings via `sentence-transformers`.
- **`backend/document_processor.py`** — Parses `.txt` course files, splits by `Lesson N:` markers, then chunks lesson text by sentence boundaries with overlap.
- **`backend/search_tools.py`** — Defines the `search_course_content` Anthropic tool and the `ToolManager` registry. Adding new tools means subclassing `Tool` and registering with `ToolManager`.
- **`backend/session_manager.py`** — In-memory conversation history. Keeps last 2 exchanges (4 messages) per session. Sessions are lost on server restart.
- **`backend/config.py`** — All tuneable settings (chunk size, overlap, max results, history length, model name) in one `Config` dataclass loaded from `.env`.

### Document format

Course `.txt` files in `docs/` must follow:
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: <title>
Lesson Link: <url>
<content>

Lesson 1: <title>
<content>
```

On startup, all files in `docs/` are indexed into ChromaDB automatically. Already-indexed courses are skipped (deduplication by title).

### Environment

Requires `ANTHROPIC_API_KEY` in a `.env` file at the repo root (see `.env.example`).

## Rules

- Use `uv run` to run Python files (e.g. `uv run python script.py`)
