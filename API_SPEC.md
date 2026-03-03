# API Specification

Base path: `/api/v1` (see `app/config.py` for `api_v1_prefix`).

All requests and responses use JSON unless stated otherwise. The service returns standard HTTP status codes:
- `200` for success
- `400` for client errors (validation, guardrail rejection)
- `404` for not found
- `500` for server errors

Endpoints

1) POST /analyze
- Description: Run a full multi-agent analysis for a single document payload.
- Content-Type: `application/json`
- Request body (example):

```json
{
  "document": {
    "content": "# Title\nThis is the manuscript text...",
    "content_type": "markdown",
    "source": "inline",
    "filename": null
  }
}
```

- Successful response: `200` with AnalysisResponse (see `app/api/models.py`). Contains `id`, `created_at`, `request`, and `result` with agent outputs and guardrails status.
- Possible errors: `400` if guardrails reject input or validation fails; `500` on internal failure.

2) POST /analyze/file
- Description: Upload a file (multipart) for analysis.
- Form parameters:
  - `file` (file, required)
  - `content_type` (string, optional; defaults to `markdown`)

- Constraints: file size limited (server-side check in `app/api/endpoints.py`). Large files will return `400`.

3) GET /history
- Description: List stored history items (only if `HISTORY_BACKEND=file`).
- Response: array of `HistoryItem` objects.

4) GET /history/{item_id}
- Description: Retrieve a single history item. Returns `404` if history is not enabled or item missing.

5) GET /history/{item_id}/export?fmt=json
- Description: Export history item as JSON. Only JSON export supported.

Notes & models
- The Pydantic models and exact field definitions live in `app/api/models.py`. Use those schemas for client validation.
- Inputs are sanitized via `app/core/safety.py` before orchestration. Guardrail failures will be surfaced as 400 responses with a message.

Authentication
- This repository does not include an auth layer by default. For production, place the service behind an authenticated gateway or add token-based auth and rate limits.

Examples
- Curl example (inline JSON):

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"document": {"content": "My draft...", "content_type": "markdown", "source":"inline"}}'
```

Observability
- Responses include consistent logging events (see `app/api/endpoints.py`) that can be parsed to correlate `analysis_id` values across logs.
