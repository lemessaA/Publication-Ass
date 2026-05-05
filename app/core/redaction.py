"""Replace common sensitive patterns before text is sent to an LLM."""

from __future__ import annotations

import re
from typing import Dict

# Rough email detector (not RFC-complete; good enough for privacy scrubbing).
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9][A-Za-z0-9._%+-]{0,63}@[A-Za-z0-9][A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# US-style and compact international-ish digit runs (avoid bare 4-digit years).
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-])?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"
    r"|(?<!\d)\+\d{10,14}\b"
)

# NIH-style (e.g. R01 CA123456) and NSF 7-digit award numbers when labeled.
_GRANT_RE = re.compile(
    r"\bR\d{2}\s?[A-Z]{2}\s?\d{6,8}\b"
    r"|(?i)\bNSF\s*[:\s-]?\s*\d{7}\b"
    r"|(?i)\b(?:grant|award)\s*#?\s*[A-Z]?\d{6,10}\b"
)


def redact_for_llm(text: str) -> tuple[str, Dict[str, int]]:
    """Replace emails, phone-like strings, and grant-like IDs with placeholders."""
    counts: Dict[str, int] = {"email": 0, "phone": 0, "grant_id": 0}

    def mark_email(_m: re.Match[str]) -> str:
        counts["email"] += 1
        return "[EMAIL]"

    def mark_phone(_m: re.Match[str]) -> str:
        counts["phone"] += 1
        return "[PHONE]"

    def mark_grant(_m: re.Match[str]) -> str:
        counts["grant_id"] += 1
        return "[GRANT_ID]"

    out = _EMAIL_RE.sub(mark_email, text)
    out = _PHONE_RE.sub(mark_phone, out)
    out = _GRANT_RE.sub(mark_grant, out)
    return out, counts


def format_redaction_warnings(counts: Dict[str, int]) -> str | None:
    """Human-readable warning line if anything was replaced."""
    parts = []
    if counts.get("email"):
        parts.append(f"{counts['email']} email-like")
    if counts.get("phone"):
        parts.append(f"{counts['phone']} phone-like")
    if counts.get("grant_id"):
        parts.append(f"{counts['grant_id']} grant-like")
    if not parts:
        return None
    joined = ", ".join(parts)
    return f"Privacy redaction applied before LLM: replaced {joined} pattern(s)."
