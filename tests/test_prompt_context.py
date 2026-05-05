from app.core.prompt_context import format_reviewer_context


def test_format_reviewer_context_empty():
    assert format_reviewer_context("") == ""
    assert format_reviewer_context("   ") == ""


def test_format_reviewer_context_nonempty():
    out = format_reviewer_context("Write for a NeurIPS reviewer.")
    assert "NeurIPS" in out
    assert out.startswith("Reviewer / audience context")
