"""Unit tests for LLM privacy redaction."""

from app.core.redaction import format_redaction_warnings, redact_for_llm


def test_redact_email() -> None:
    text, counts = redact_for_llm("Write to a@b.co for details.")
    assert "[EMAIL]" in text
    assert "a@b.co" not in text
    assert counts["email"] == 1
    assert format_redaction_warnings(counts) is not None


def test_redact_phone_us() -> None:
    text, counts = redact_for_llm("Call (555) 123-4567 today.")
    assert "[PHONE]" in text
    assert "555" not in text
    assert counts["phone"] >= 1


def test_redact_nsf_grant() -> None:
    text, counts = redact_for_llm("Supported by NSF 1234567.")
    assert "[GRANT_ID]" in text
    assert "1234567" not in text
    assert counts["grant_id"] >= 1


def test_no_false_positive_empty_counts() -> None:
    text, counts = redact_for_llm("No secrets here; only prose.")
    assert text == "No secrets here; only prose."
    assert sum(counts.values()) == 0
    assert format_redaction_warnings(counts) is None
