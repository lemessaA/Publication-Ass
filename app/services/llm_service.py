from __future__ import annotations

from langchain_groq import ChatGroq

from app.config import get_settings


def build_llm() -> ChatGroq:
    """Create the shared Groq LLM instance for all agents."""
    settings = get_settings()
    # ChatGroq reads GROQ_API_KEY from the environment, but we also pass it explicitly
    # via the client initialization to keep configuration centralized.
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key or None,
        temperature=0.2,
    )

