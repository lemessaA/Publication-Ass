from __future__ import annotations

import re

from app.api.models import AnalysisRequest, GuardrailResult, GuardrailStatus
from app.config import get_settings


def apply_guardrails(request: AnalysisRequest) -> GuardrailResult:
    """Very lightweight content filtering guardrail."""
    settings = get_settings()
    content = request.document.content

    if len(content) > settings.max_input_chars:
        return GuardrailResult(
            status=GuardrailStatus.rejected,
            reason=f"Document too long (>{settings.max_input_chars} chars).",
            details={"length": len(content)},
        )

    # Simple sensitive token detection (you can extend this significantly).
    banned_patterns = [
        r"PRIVATE[_-]?KEY",
        r"BEGIN RSA PRIVATE KEY",
        r"AKIA[0-9A-Z]{16}",  # AWS access key pattern
    ]
    for pattern in banned_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return GuardrailResult(
                status=GuardrailStatus.rejected,
                reason="Potentially sensitive credentials detected.",
                details={"pattern": pattern},
            )

    return GuardrailResult(status=GuardrailStatus.ok)

