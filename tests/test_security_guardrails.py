"""
Security and guardrail tests for the analysis API.

These tests confirm that sensitive content is rejected and file size
limits / other safety-related checks are enforced by the API guardrails.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_guardrails_reject_sensitive_tokens() -> None:
    resp = client.post(
        "/api/v1/analyze",
        json={
            "document": {
                "content": "Here is my key: BEGIN RSA PRIVATE KEY",
                "content_type": "markdown",
                "source": "text",
            }
        },
    )
    assert resp.status_code in (400, 422)


def test_file_size_limit_enforced() -> None:
    big = b"a" * 6_000_000
    resp = client.post(
        "/api/v1/analyze/file",
        data={"content_type": "markdown"},
        files={"file": ("big.txt", big, "text/plain")},
    )
    assert resp.status_code == 400
