from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import router as api_router
from app.config import get_settings
from app.logging_config import configure_logging


configure_logging()
settings = get_settings()

app = FastAPI(
    title="Publication Assistant for AI Projects",
    version="1.0.0",
    description="Multi-agent assistant for improving AI/ML publications.",
)

# CORS for Streamlit front-end.
if settings.allowed_origin:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.allowed_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)

# Serve built frontend static files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")


@app.get("/healthz")
async def healthcheck():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

