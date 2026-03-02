# Publication Assistant (Groq + FastAPI + Streamlit)

A lightweight multi-agent assistant that analyzes AI/ML publication drafts for:
- clarity improvements
- structure/outline suggestions
- technical review feedback
- visual/figure/table suggestions
- abstract + key contributions
- titles + keyword tags

It includes:
- a **FastAPI** backend (`/api/v1/...`) that runs the analysis pipeline
- a **Streamlit** UI that calls the backend
- an LLM integration configured for **Groq**

---

## Project structure

```text
publication-Ass/
  app/
    agents/              # clarity/structure/technical/visual/summary/tag agents
    api/                 # request/response models + endpoints
    core/                # orchestrator (LangGraph) + guardrails
    services/            # LLM provider wrapper + history storage
    main.py              # FastAPI app entrypoint
    config.py            # env-based settings
  streamlit_app/
    main.py              # Streamlit UI
  tests/
    test_api.py
    test_agents.py
  requirements.txt
```

---

## Requirements

- Python **3.10+** (recommended)
- A **Groq API key**

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration (Groq)

Set your Groq API key:

```bash
export GROQ_API_KEY="your_groq_api_key"
```

Optional: pick a Groq model (default is `llama-3.1-70b-versatile`):

```bash
export GROQ_MODEL="llama-3.1-70b-versatile"
```

Other optional env vars:
- `FRONTEND_ORIGIN`: enables CORS for the Streamlit app (e.g. `http://localhost:8501`)
- `HISTORY_BACKEND`: `memory` (default) or `file`
- `HISTORY_DIR`: folder where history JSON is stored (when `HISTORY_BACKEND=file`)

---

## Run the backend (FastAPI)

From the project root:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Healthcheck:

```bash
curl http://localhost:8000/healthz
```

API base prefix is `"/api/v1"` (see `app/config.py`).

---

## Run the frontend (Streamlit)

In a separate terminal:

```bash
export BACKEND_URL="http://localhost:8000"
streamlit run streamlit_app/main.py
```

Then open Streamlit in your browser (Streamlit will print the local URL).

---

## API endpoints (backend)

- `POST /api/v1/analyze` — analyze pasted text (JSON body)
- `POST /api/v1/analyze/file` — analyze uploaded file (`multipart/form-data`)
- `GET /api/v1/history` — list history items (only when `HISTORY_BACKEND=file`)
- `GET /api/v1/history/{item_id}` — fetch one history item (file backend only)
- `GET /api/v1/history/{item_id}/export?fmt=json` — export one history item

---

## Running tests

```bash
pytest -q
```

---

## Troubleshooting

### LLM calls fail / empty output
- Ensure `GROQ_API_KEY` is set in the same shell where you run `uvicorn`.
- If you use an `.env` file, export the variables or use a tool like `direnv`.

### Streamlit shows “Backend error”
- Confirm the backend is running and reachable at `BACKEND_URL`.
- Check the backend logs for the underlying exception.

---

## Notes

This project is intentionally minimal and designed to be easy to extend (e.g., richer guardrails, better JSON parsing, streaming results, additional agents, persistent storage).
