"""
API integration tests exercising the FastAPI endpoints.

These tests use `TestClient` to verify healthchecks, validation behavior,
file uploads, and that the analysis endpoint integrates with the
orchestrator (the LLM is monkeypatched in tests to avoid network calls).
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"


def test_analyze_validation_error() -> None:
    # Missing required `document` field should trigger validation error.
    resp = client.post("/api/v1/analyze", json={})
    assert resp.status_code in (400, 422)


def test_analyze_happy_path(monkeypatch, fake_llm) -> None:
    import app.core.orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "build_llm", lambda: fake_llm)

    resp = client.post(
        "/api/v1/analyze",
        json={
            "document": {
                "content": "Hello world",
                "content_type": "markdown",
                "source": "text",
            }
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["guardrails"]["status"] == "ok"


def test_analyze_redaction_json(monkeypatch, fake_llm) -> None:
    import app.core.orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "build_llm", lambda: fake_llm)

    resp = client.post(
        "/api/v1/analyze",
        json={
            "document": {
                "content": "Hello reach me at nobody@example.org thanks.",
                "content_type": "markdown",
                "source": "text",
            },
            "redact_before_llm": True,
        },
    )
    assert resp.status_code == 200
    warns = resp.json()["result"].get("analysis_warnings") or []
    assert any("redaction" in w.lower() for w in warns)


def test_analyze_stream_sse(monkeypatch, fake_llm) -> None:
    import app.core.orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "build_llm", lambda: fake_llm)

    with client.stream(
        "POST",
        "/api/v1/analyze/stream",
        json={
            "document": {
                "content": "Hello world",
                "content_type": "markdown",
                "source": "text",
            }
        },
    ) as resp:
        assert resp.status_code == 200
        raw = "".join(resp.iter_text())

    assert "data:" in raw
    assert '"type": "step"' in raw or '"type":"step"' in raw.replace(" ", "")
    assert '"type": "complete"' in raw or '"type":"complete"' in raw.replace(" ", "")
    assert "guardrails" in raw


def test_analyze_file_upload(monkeypatch, fake_llm) -> None:
    import app.core.orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "build_llm", lambda: fake_llm)

    resp = client.post(
        "/api/v1/analyze/file",
        data={"content_type": "markdown"},
        files={"file": ("test.md", b"# Title\ncontent", "text/markdown")},
    )
    assert resp.status_code == 200


def test_analyze_section_scope_json(monkeypatch, fake_llm) -> None:
    import app.core.orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "build_llm", lambda: fake_llm)

    doc = "L1\nL2\nL3\nL4\n"
    resp = client.post(
        "/api/v1/analyze",
        json={
            "document": {
                "content": doc,
                "content_type": "markdown",
                "source": "text",
            },
            "section_scope": {"start_line": 2, "end_line": 3},
            "section_hint": "Methods draft",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["guardrails"]["status"] == "ok"
    warns = data["result"].get("analysis_warnings") or []
    assert any("lines 2" in w for w in warns)
