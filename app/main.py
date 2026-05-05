from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import router as api_router
from app.config import get_settings
from app.logging_config import configure_logging


configure_logging()
settings = get_settings()

# Built SPA lives at repo root `static/` (see README / Dockerfile). Always resolve from this file,
# not the process cwd, so `fastapi dev` works from any directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_STATIC_DIR = _REPO_ROOT / "static"

app = FastAPI(
    title="Publication Assistant for AI Projects",
    version="1.0.0",
    description="Multi-agent assistant for improving AI/ML publications.",
)

# CORS for the Vite/React front-end (see FRONTEND_ORIGIN).
if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)

# Serve built frontend static files when present (optional in local API-only dev).
if _STATIC_DIR.is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=str(_STATIC_DIR), html=True),
        name="static",
    )


@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse

    index = _STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Web UI bundle not found.",
            "hint": "Build the frontend and copy dist to ./static at the repo root, or use the Vite dev server (npm run dev in frontend/) pointing at this API.",
            "api_docs": "/docs",
            "health": "/healthz",
        },
    )


@app.get("/healthz")
async def healthcheck():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
