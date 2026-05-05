from __future__ import annotations

import re
from typing import Iterable

from app.api.models import (
    AnalysisResult,
    ClarityFeedback,
    StructureFeedback,
    TechnicalFeedback,
    VisualFeedback,
    SummaryFeedback,
    TagFeedback,
)


_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key ID
    re.compile(r"BEGIN RSA PRIVATE KEY", re.IGNORECASE),
    re.compile(r"PRIVATE[_-]?KEY", re.IGNORECASE),
    # Common API key prefixes (best-effort)
    re.compile(r"\bgsk_[A-Za-z0-9]{20,}\b"),  # Groq-style
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),  # OpenAI-style
]


def sanitize_input_text(text: str) -> str:
    # Avoid surprising behavior with null bytes and odd whitespace
    text = text.replace("\x00", "")
    return text.strip()


def _redact(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def redact_strings(values: Iterable[str]) -> list[str]:
    return [_redact(v) for v in values]


def filter_analysis_result(result: AnalysisResult) -> AnalysisResult:
    """Best-effort output filtering: redact secrets and tidy noisy LLM text."""
    r = result.model_copy(deep=True)

    if r.clarity:
        r.clarity = ClarityFeedback(
            improved_text=_polish_multiline(_redact(r.clarity.improved_text), 120_000),
            comments=_polish_string_list(r.clarity.comments, 4_000),
        )

    if r.structure:
        r.structure = StructureFeedback(
            suggested_outline=_polish_string_list(r.structure.suggested_outline, 2_000),
            section_suggestions=_polish_string_list(r.structure.section_suggestions, 4_000),
        )

    if r.technical:
        r.technical = TechnicalFeedback(
            issues_found=_polish_paragraph_list(r.technical.issues_found, 6_000),
            suggestions=_polish_paragraph_list(r.technical.suggestions, 6_000),
            overall_confidence=r.technical.overall_confidence,
        )

    if r.visuals:
        r.visuals = VisualFeedback(
            suggestions=[
                s.model_copy(
                    update={
                        "title": _polish_single_line(_redact(s.title), 400),
                        "description": _polish_single_line(_redact(s.description), 4_000),
                        "type": _polish_single_line(_redact(s.type), 120),
                    }
                )
                for s in r.visuals.suggestions
            ],
            formatting_tips=_polish_string_list(r.visuals.formatting_tips, 3_000),
        )

    if r.summary:
        r.summary = SummaryFeedback(
            summary=_polish_multiline(_redact(r.summary.summary), 12_000),
            key_contributions=_polish_string_list(r.summary.key_contributions, 2_000),
        )

    if r.tags:
        r.tags = TagFeedback(
            title_suggestions=_polish_string_list(r.tags.title_suggestions, 400),
            tags=_polish_string_list(r.tags.tags, 200),
        )

    return r


def _polish_single_line(text: str, max_chars: int) -> str:
    s = re.sub(r"\s+", " ", text.strip())
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rsplit(" ", 1)[0] + "…" if " " in s[:max_chars] else s[: max_chars - 1] + "…"


def _polish_multiline(text: str, max_chars: int) -> str:
    s = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n{4,}", "\n\n\n", s)
    if len(s) <= max_chars:
        return s
    head = s[: max_chars - 1]
    cut = head.rsplit("\n\n", 1)[0] if "\n\n" in head else head.rsplit(" ", 1)[0]
    return cut + "…"


def _polish_paragraph_list(values: Iterable[str], max_each: int) -> list[str]:
    out: list[str] = []
    for v in values:
        block = _polish_multiline(_redact(str(v)), max_each)
        if block:
            out.append(block)
    return out


def _polish_string_list(values: Iterable[str], max_each: int) -> list[str]:
    out: list[str] = []
    for v in values:
        line = _polish_single_line(_redact(str(v)), max_each)
        if line:
            out.append(line)
    return out

