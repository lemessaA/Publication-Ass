"""Shared prompt fragments for agents (e.g. reviewer persona from config)."""


def format_reviewer_context(persona: str) -> str:
    """Return a prefix block for LLM prompts, or empty string if unset."""
    text = (persona or "").strip()
    if not text:
        return ""
    return (
        "Reviewer / audience context (follow in addition to all instructions below):\n"
        f"{text}\n\n"
        "---\n\n"
    )
