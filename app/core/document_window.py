"""Shrink documents to fit provider context limits (Groq rejects oversized prompts)."""

from __future__ import annotations

_SEPARATOR = (
    "\n\n---\n[Middle omitted: document shortened to fit the language model "
    "context limit.]\n---\n\n"
)


def window_document_for_llm(content: str, max_chars: int) -> tuple[str, bool]:
    """Return content possibly shortened for LLM calls.

    Uses head + tail so intro/conclusions remain visible.
    Returns (text, was_truncated).
    """
    if max_chars <= 0:
        return "", False
    if len(content) <= max_chars:
        return content, False

    sep_len = len(_SEPARATOR)
    usable = max_chars - sep_len
    if usable < 80:
        return content[:max_chars], True

    head_chars = max(40, int(usable * 0.58))
    tail_chars = usable - head_chars
    head = content[:head_chars]
    tail = content[-tail_chars:] if tail_chars > 0 else ""
    out = head + _SEPARATOR + tail
    if len(out) > max_chars:
        out = out[:max_chars]
    return out, True
