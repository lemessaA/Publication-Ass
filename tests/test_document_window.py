from app.core.document_window import window_document_for_llm


def test_no_truncation_when_short():
    s = "hello"
    out, truncated = window_document_for_llm(s, 100)
    assert out == s
    assert truncated is False


def test_truncation_window():
    s = "a" * 1000
    out, truncated = window_document_for_llm(s, 200)
    assert truncated is True
    assert len(out) <= 200
    assert "Middle omitted" in out
    assert out.startswith("aaa")


def test_empty_max_returns_empty():
    out, truncated = window_document_for_llm("hello", 0)
    assert out == ""
    assert truncated is False
