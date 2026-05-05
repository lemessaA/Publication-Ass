"""Tests for section-scoped document slicing."""

import pytest

from app.api.models import AnalysisRequest, DocumentInput, SectionScope
from app.core.section_extract import slice_document_for_section_analysis


def test_slice_middle_lines() -> None:
    content = "a\nb\nc\nd\ne\n"
    text, warns = slice_document_for_section_analysis(
        content, SectionScope(start_line=2, end_line=4)
    )
    assert text == "b\nc\nd"
    assert any("lines 2–4" in w for w in warns)


def test_trim_end_past_document() -> None:
    content = "only\n"
    text, warns = slice_document_for_section_analysis(
        content, SectionScope(start_line=1, end_line=99)
    )
    assert text == "only"
    assert any("trimmed" in w.lower() for w in warns)


def test_start_beyond_document_raises() -> None:
    content = "one\n"
    try:
        slice_document_for_section_analysis(content, SectionScope(start_line=5, end_line=6))
    except ValueError as exc:
        assert "beyond" in str(exc).lower() or "beyond" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_analysis_request_validator_out_of_range() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AnalysisRequest(
            document=DocumentInput(content="x\ny\n", content_type="markdown", source="text"),
            section_scope=SectionScope(start_line=10, end_line=11),
        )
