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
