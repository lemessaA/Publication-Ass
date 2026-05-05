# Deployment: Render (API) + Vercel (frontend)

This guide wires the **FastAPI backend on [Render](https://render.com)** and the **Vite React app on [Vercel](https://vercel.com)**. The browser calls the Render API over HTTPS; CORS must allow your Vercel origin(s). JSON and **SSE streaming** (`/analyze/stream`, `/analyze/file/stream`) use the same CORS rules.

### At a glance

| Piece | Where | Must set |
|--------|--------|-----------|
| API | Render Web Service | `GROQ_API_KEY`, `FRONTEND_ORIGIN` |
| UI | Vercel (`frontend/` root) | `VITE_API_BASE_URL` = `https://<render-host>/api/v1` |

**Order:** deploy Render → copy API URL → set Vercel env → deploy Vercel → set `FRONTEND_ORIGIN` on Render to your Vercel URL → redeploy Render if needed.

**Alternative:** run everything from one URL using the repo **`Dockerfile`** (FastAPI serves the built SPA under `/`). See §5.

---

## 1. Deploy the backend (Render)

### Option A — Blueprint (`render.yaml`)

1. Push this repository to GitHub/GitLab.
2. In Render: **New** → **Blueprint** → connect the repo → select `render.yaml`.
3. After the first deploy, open the web service → **Environment** and set:
   - **`GROQ_API_KEY`** — your Groq API key (required).
   - **`FRONTEND_ORIGIN`** — your Vercel URL(s), comma-separated if you need more than one (see below).

Render injects **`PORT`**; the start command uses **`uvicorn ... --port $PORT`**.

Health check: **`GET /healthz`** (configured in `render.yaml`).

### Option B — Manual Web Service

1. **New** → **Web Service** → connect the repo.
2. **Runtime:** Python  
   **Root directory:** repository root (where `pyproject.toml` lives).  
   **Build command:** `pip install .`  
   **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add the same environment variables as in the blueprint (at minimum `GROQ_API_KEY`, `FRONTEND_ORIGIN`, `ENVIRONMENT=production`).
4. Optional: set **Python version** to **3.12** (matches `render.yaml` / `Dockerfile`).

### Production env reference (Render)

| Variable | Required | Notes |
|----------|-----------|--------|
| `GROQ_API_KEY` | Yes | Groq API key. |
| `FRONTEND_ORIGIN` | Yes for browser UI | Comma-separated origins, e.g. `https://your-app.vercel.app`. No trailing slash. |
| `ENVIRONMENT` | Recommended | `production` |
| `GROQ_MODEL` | Optional | Default in `app/config.py` / `render.yaml`. |
| `MAX_LLM_INPUT_CHARS` | Optional | Lower if Groq returns 413 / token limit errors. |
| `MAX_INPUT_CHARS` | Optional | Max pasted/upload size for guardrails (characters). |
| `REVIEWER_PERSONA` | Optional | Prepended to every agent; restart service after change. |
| `HISTORY_BACKEND` | Optional | `memory` (default on Render) or `file` + disk mount — see §6. |

Secrets (`GROQ_API_KEY`) should be set in the Render dashboard or secret store, not committed.

### Backend URL

After deploy, note the public URL, e.g. `https://publication-assistant-api.onrender.com`.

The frontend must call **`https://<your-render-host>/api/v1`** (the app already uses the `/api/v1` prefix).

---

## 2. CORS (`FRONTEND_ORIGIN`)

The API reads **`FRONTEND_ORIGIN`** as a **comma-separated** list (no spaces required, but they are trimmed):

```text
https://your-app.vercel.app,https://your-app-git-main-team.vercel.app
```

- Set **production** to your primary Vercel domain (e.g. `https://my-app.vercel.app` or your custom domain).
- For **preview deployments**, either add each preview URL after first deploy or temporarily use only the production URL while testing.

If `FRONTEND_ORIGIN` is empty, **no CORS middleware** is registered (fine for server-side-only or same-origin setups).

---

## 3. Deploy the frontend (Vercel)

1. Import the **same Git repository** into Vercel.
2. **Root Directory:** `frontend` (important: `package.json` is under `frontend/`).
3. Framework: **Vite** (auto-detected from `frontend/package.json`).
4. **Environment variables** (Production — and Preview if you test against a staging API):

   | Name | Example value |
   |------|----------------|
   | `VITE_API_BASE_URL` | `https://publication-assistant-api.onrender.com/api/v1` |

   Use your real Render hostname and **always include `/api/v1`** at the end.

5. Deploy. Open the Vercel URL and run an analysis; if the browser shows CORS errors, fix **`FRONTEND_ORIGIN`** on Render to match the exact Vercel origin (scheme + host, no trailing slash).

---

## 4. Order of operations

1. Deploy **Render** first (or at least know the future API URL).
2. Set **`VITE_API_BASE_URL`** on Vercel to `https://<render-host>/api/v1`.
3. Deploy **Vercel**.
4. Set **`FRONTEND_ORIGIN`** on Render to your Vercel production URL (and previews if needed).
5. Redeploy Render if you change env vars (or use Render’s env reload behavior).

---

## 5. Optional: single Docker image (Render or elsewhere)

The repo root **`Dockerfile`** builds the frontend and copies `dist` into **`static/`** so FastAPI serves the SPA at **`/`**. That pattern hosts UI + API on **one** URL; it is **not** what this guide uses for **Vercel + Render split**. To use Docker on Render instead, create a **Docker** web service pointing at that Dockerfile and set **`PORT`**, **`GROQ_API_KEY`**, and optionally **`FRONTEND_ORIGIN`** (omit or leave empty when the browser only talks to the same origin).

---

## 6. History storage on Render

Default **`HISTORY_BACKEND=memory`** loses data on restarts. For persistent file history you’d mount a **Render disk** and set **`HISTORY_BACKEND=file`** and **`HISTORY_DIR`** to a path on that disk (see `app/config.py`). For serverless-style deploys, **memory** is usually enough.

---

## 7. Troubleshooting

- **CORS errors in the browser** — `FRONTEND_ORIGIN` must match the **exact** page origin (scheme + host, no path). Include preview URLs separately if you test previews against prod API.
- **Analyze fails / wrong host** — Confirm `VITE_API_BASE_URL` ends with **`/api/v1`** and was set **before** the Vercel build (redeploy after changing env).
- **413 / payload too large from Groq** — Reduce pasted length or lower **`MAX_LLM_INPUT_CHARS`** on Render; use **section scope** in the UI for long papers.
- **Cold starts (free tier)** — First request after idle can take tens of seconds; subsequent requests are faster.

---

## 8. Checklist

- [ ] `GROQ_API_KEY` set on Render  
- [ ] `FRONTEND_ORIGIN` matches Vercel origin(s) exactly  
- [ ] `VITE_API_BASE_URL` on Vercel = `https://<render-host>/api/v1`  
- [ ] `GET https://<render-host>/healthz` returns `200`  
- [ ] Browser network tab: API calls go to Render, not `localhost`
