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
    """Best-effort output filtering to avoid returning secrets in responses."""
    r = result.model_copy(deep=True)

    if r.clarity:
        r.clarity = ClarityFeedback(
            improved_text=_redact(r.clarity.improved_text),
            comments=redact_strings(r.clarity.comments),
        )

    if r.structure:
        r.structure = StructureFeedback(
            suggested_outline=redact_strings(r.structure.suggested_outline),
            section_suggestions=redact_strings(r.structure.section_suggestions),
        )

    if r.technical:
        r.technical = TechnicalFeedback(
            issues_found=redact_strings(r.technical.issues_found),
            suggestions=redact_strings(r.technical.suggestions),
            overall_confidence=r.technical.overall_confidence,
        )

    if r.visuals:
        r.visuals = VisualFeedback(
            suggestions=[
                s.model_copy(
                    update={
                        "title": _redact(s.title),
                        "description": _redact(s.description),
                        "type": _redact(s.type),
                    }
                )
                for s in r.visuals.suggestions
            ],
            formatting_tips=redact_strings(r.visuals.formatting_tips),
        )

    if r.summary:
        r.summary = SummaryFeedback(
            summary=_redact(r.summary.summary),
            key_contributions=redact_strings(r.summary.key_contributions),
        )

    if r.tags:
        r.tags = TagFeedback(
            title_suggestions=redact_strings(r.tags.title_suggestions),
            tags=redact_strings(r.tags.tags),
        )

    return r

