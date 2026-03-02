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

