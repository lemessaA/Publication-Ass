from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """Application-wide configuration settings."""

    # API
    api_v1_prefix: str = "/api/v1"

    # LLM / LangChain configuration (Groq)
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = Field(
        default=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        description="Groq model name to use for all LLM calls.",
    )
    # app/config.py

    # Backendopenai/gpt-oss-20b
    environment: str = Field(default=os.getenv("ENVIRONMENT", "development"))
    debug: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true")

    # Frontend
    allowed_origin: str | None = Field(default=os.getenv("FRONTEND_ORIGIN", None))

    # Simple history storage (file-based path or "memory")
    history_backend: str = Field(default=os.getenv("HISTORY_BACKEND", "memory"))
    history_dir: str = Field(default=os.getenv("HISTORY_DIR", "./history"))

    # Basic content guardrails
    max_input_chars: int = 200000


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        # In a real deployment, you'd likely log this and fail fast.
        raise RuntimeError(f"Invalid application settings: {e}") from e

