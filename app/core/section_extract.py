"""Extract a line range from document text for section-scoped analysis."""

from __future__ import annotations

from app.api.models import SectionScope


def slice_document_for_section_analysis(
    content: str,
    scope: SectionScope,
) -> tuple[str, list[str]]:
    """Return (slice text, non-fatal warnings). Raises ValueError if the slice is unusable."""
    lines = content.splitlines()
    n = len(lines)
    start = scope.start_line
    end = scope.end_line

    if n == 0:
        raise ValueError("Document has no lines to analyze.")

    if start > n:
        raise ValueError(
            f"start_line ({start}) is beyond the document ({n} line{'s' if n != 1 else ''})."
        )

    effective_end = min(end, n)
    if effective_end < start:
        raise ValueError("end_line is before start_line after clipping to the document.")

    slice_lines = lines[start - 1 : effective_end]
    text = "\n".join(slice_lines).strip()
    if not text:
        raise ValueError("Selected line range contains only blank lines.")

    warnings: list[str] = []
    if effective_end < end:
        warnings.append(
            f"end_line was trimmed from {end} to {effective_end} (end of pasted document)."
        )
    warnings.append(
        f"Analyzing lines {start}–{effective_end} only ({len(slice_lines)} lines from the paste)."
    )
    return text, warnings
