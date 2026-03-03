# Troubleshooting & FAQ

This document lists common issues, symptoms, and recovery steps.

1) CORS errors from the frontend
- Symptom: Browser console shows CORS blocked when calling the backend.
- Cause: `FRONTEND_ORIGIN` not set or mismatched.
- Recovery: Set `FRONTEND_ORIGIN` to your Vite URL (e.g., `http://localhost:5173`) in the environment and restart the backend.

2) `GROQ_API_KEY` missing / LLM errors
- Symptom: Requests return 500 with LLM errors or responses are empty/invalid.
- Cause: API key missing, invalid, or provider rate-limited.
- Recovery: Ensure `GROQ_API_KEY` is defined in the environment (or `.env`). Check outbound connectivity and provider status.

3) Uploaded file rejected or "too large"
- Symptom: `400: Uploaded file is too large.`
- Cause: Server-side upload limit enforced in the endpoint.
- Recovery: Reduce file size, split the document, or increase limit in code with care.

4) History endpoints return 404
- Symptom: `GET /history` returns 404 or empty results.
- Cause: `HISTORY_BACKEND` is set to `memory` (file history disabled) or history dir missing.
- Recovery: Set `HISTORY_BACKEND=file` and ensure `HISTORY_DIR` exists and is writable.

5) Guardrails reject content
- Symptom: `400` with reason containing guardrail message.
- Cause: Input violates configured guardrails (safety/content rules).
- Recovery: Inspect the returned detail message, sanitize or shorten the input, or adjust guardrail rules carefully.

6) Persistent errors after code changes
- Symptom: Unexpected 500s after edits or dependency upgrades.
- Recovery: Run tests with `pytest`, check stack traces in logs, and revert to the last known good commit if necessary.

7) Performance / slow responses
- Symptom: Long analysis times.
- Causes: LLM latency, large inputs, or synchronous blocking steps.
- Mitigations: Increase LLM parallelism (if supported), limit input size, add batching, or move expensive steps to background jobs with a task queue.

FAQ
- Q: Where are request/response schemas defined?
  - A: See `app/api/models.py` for Pydantic schemas.
- Q: How do I switch LLM providers?
  - A: Implement or update `app/services/llm_service.py` and validate any prompt-format changes.

When to open an issue
- If you hit reproducible errors after following this guide and logs do not indicate a clear cause, open an issue including: minimal repro, requests made, relevant log lines, and environment variables used (omit secrets).
