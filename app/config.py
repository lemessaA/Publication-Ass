from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

load_dotenv()


def _parse_allowed_origins() -> list[str]:
    """Comma-separated FRONTEND_ORIGIN; trim whitespace and trailing slashes (browser Origins have none)."""
    raw = os.getenv("FRONTEND_ORIGIN") or ""
    out: list[str] = []
    for part in raw.split(","):
        s = part.strip()
        if not s:
            continue
        s = s.rstrip("/")
        out.append(s)
    return out


class Settings(BaseModel):
    """Application-wide configuration settings."""

    # API
    api_v1_prefix: str = "/api/v1"

    # LLM / LangChain configuration (Groq)
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = Field(
        default=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        description="Groq model name to use for all LLM calls.",
    )

    environment: str = Field(default=os.getenv("ENVIRONMENT", "development"))
    debug: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true")

    # Frontend — comma-separated URLs for CORS (e.g. prod + Vercel preview)
    allowed_origins: list[str] = Field(default_factory=lambda: _parse_allowed_origins())

    # Simple history storage (file-based path or "memory")
    history_backend: str = Field(default=os.getenv("HISTORY_BACKEND", "memory"))
    history_dir: str = Field(default=os.getenv("HISTORY_DIR", "./history"))

    # Basic content guardrails (upload / paste maximum)
    max_input_chars: int = Field(default=int(os.getenv("MAX_INPUT_CHARS", "200000")))
    # Groq rejects oversized prompts (HTTP 413 / token limits). Window document for LLM calls.
    max_llm_input_chars: int = Field(
        default=int(os.getenv("MAX_LLM_INPUT_CHARS", "24000")),
        description="Max characters sent to the LLM (head+tail window). Increase only if your Groq tier/model allows.",
    )

    # Prepended to every agent prompt (tone, venue, audience). Empty = default prompts only.
    reviewer_persona: str = Field(
        default=os.getenv("REVIEWER_PERSONA", "").strip(),
        description="Optional instructions for all reviewers (e.g. strict NeurIPS-style vs student thesis).",
    )


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        # In a real deployment, you'd likely log this and fail fast.
        raise RuntimeError(f"Invalid application settings: {e}") from e

