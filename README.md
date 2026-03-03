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

# Dependencies
pip install -r requirements.txt

# Run (dev)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to calling `http://localhost:8000/api/v1`. Override with `VITE_API_BASE_URL` in `frontend/.env` if needed.

---

## Environment variables

Create a `.env` file in the project root or set in your shell:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
GROQ_MODEL=openai/gpt-oss-120b
FRONTEND_ORIGIN=http://localhost:5173          # Enables CORS for the frontend
HISTORY_BACKEND=memory                         # or "file"
HISTORY_DIR=./history
ENVIRONMENT=development
DEBUG=false
```

---

## API reference

Base URL: `http://localhost:8000/api/v1`

- `POST /analyze` – Analyze raw text (JSON)
- `POST /analyze/file` – Analyze uploaded file (multipart)
- `GET /healthz` – Health check

See `app/api/endpoints.py` and `app/api/models.py` for schemas.

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

---

## Troubleshooting

- **CORS errors**: Set `FRONTEND_ORIGIN` to your Vite dev URL (e.g., `http://localhost:5173`) and restart the backend.
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
