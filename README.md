# Publication Assistant for AI Projects

A multi-agent assistant that analyzes AI/ML publication drafts and provides actionable feedback across clarity, structure, technical soundness, visuals, abstracts, and tags.

**Tech stack**
- Backend: FastAPI + LangGraph orchestration
- LLM: Groq (via LangChain)
- Frontend: React + Vite (TypeScript)
- Tests: pytest

---

## Features

- **Clarity**: Improved phrasing and readability comments
- **Structure**: Outline and section suggestions
- **Technical review**: Issues found and suggestions for methodology/experiments
- **Visuals**: Diagram/figure/table recommendations
- **Summary**: Draft abstract and key contributions
- **Tags**: Title candidates and keyword tags
- **Guardrails**: Basic content checks before analysis

---

## Quickstart

### Prerequisites
- Python 3.10+
- Node.js (npm/pnpm)

### Backend
```bash
# Virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Dependencies (PEP 621, see `pyproject.toml` in the repo root)
pip install -e .

# Run (dev, from repository root)
# Option A — FastAPI CLI (reload + dev defaults)
fastapi dev app/main.py --host 0.0.0.0

# Option B — Uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to calling `http://localhost:8000/api/v1`. Override with `VITE_API_BASE_URL` in `frontend/.env.local` or copy `frontend/.env.example` as a starting point.

### Serving the UI from FastAPI (production-style)

The API serves a built SPA from a `static/` directory at the repo root (`/` and `/static/…`). After building the frontend, copy the Vite output into `static/` so it matches what the Docker image does:

```bash
cd frontend && npm run build
mkdir -p ../static && cp -r dist/* ../static/
```

Then run `uvicorn` as above and open `http://localhost:8000/`.

---

## Environment variables

Create a `.env` file in the project root or set in your shell:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
GROQ_MODEL=openai/gpt-oss-120b
FRONTEND_ORIGIN=http://localhost:5173    # CORS: comma-separated origins in production (see DEPLOYMENT.md)
HISTORY_BACKEND=memory                         # or "file"
HISTORY_DIR=./history
ENVIRONMENT=development
DEBUG=false
MAX_INPUT_CHARS=200000                      # Max paste/upload size for guardrails (characters)
MAX_LLM_INPUT_CHARS=24000                    # Max chars sent to Groq per request (head+tail window); lower if you hit 413/token limits
REVIEWER_PERSONA=                            # Optional tone/audience for all agents (e.g. strict venue vs thesis). See FEATURE_ROADMAP.md.
```

**Feature roadmap (step-by-step plans):** [`FEATURE_ROADMAP.md`](FEATURE_ROADMAP.md).

**Production (Render + Vercel):** see [`DEPLOYMENT.md`](DEPLOYMENT.md) for `VITE_API_BASE_URL`, `FRONTEND_ORIGIN`, and platform env setup.

---

## API reference

API base URL: `http://localhost:8000/api/v1`

- `POST /analyze` – Analyze raw text (JSON)
- `POST /analyze/stream` – Same analysis as `POST /analyze`, streamed as SSE (`text/event-stream`) with per-node `step` events and a final `complete` payload
- `POST /analyze/file` – Analyze uploaded file (multipart)
- `POST /analyze/file/stream` – File upload with SSE progress + final `complete` event
- `GET /history` – List saved analyses (only when `HISTORY_BACKEND=file`)
- `GET /history/{id}` – Load one saved analysis

Health check (not under `/api/v1`): `GET http://localhost:8000/healthz`

See `app/api/endpoints.py`, `app/api/models.py`, and `API_SPEC.md` for schemas.

---

## Development

### Tests
```bash
pytest -q
```

### Adding agents
- Implement new agents under `app/agents/`
- Register in the orchestrator (`app/core/orchestrator.py`)

### Switching LLM provider
- Update `app/services/llm_service.py` and `app/config.py`

### Deployment notes

- There is no built-in authentication or rate limiting; put the service behind a reverse proxy or API gateway with TLS, auth, and throttling if it is exposed on the internet.
- **Render (API) + Vercel (UI):** step-by-step guide in [`DEPLOYMENT.md`](DEPLOYMENT.md). The frontend build needs `VITE_API_BASE_URL=https://<your-render-host>/api/v1`; the API needs `FRONTEND_ORIGIN` listing your Vercel URL(s), comma-separated if needed.
---

## Troubleshooting

- **CORS errors**: Set `FRONTEND_ORIGIN` to your frontend origin(s)—comma-separated if you have several (e.g. Vercel prod + preview). Restart the backend after changes.
- **Failed to fetch**: Ensure the backend is running on the expected host/port and that `VITE_API_BASE_URL` matches.
- **LLM failures**: Verify `GROQ_API_KEY` is set and outbound network is allowed.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new behavior
4. Open a pull request

---

## License

MIT
