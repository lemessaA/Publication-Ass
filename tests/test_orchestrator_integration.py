"""
Integration tests for the orchestrator flow in `app.core.orchestrator`.

These tests exercise end-to-end orchestration of multiple agents and
validate graceful degradation when individual agents fail. They patch
`build_llm` to use the local `fake_llm` fixture.
"""

from __future__ import annotations

import app.core.orchestrator as orchestrator
from app.api.models import AnalysisRequest, DocumentInput


def test_orchestrator_runs_all_agents(monkeypatch, fake_llm) -> None:
    monkeypatch.setattr(orchestrator, "build_llm", lambda: fake_llm)

    req = AnalysisRequest(
        document=DocumentInput(content="Hello world", content_type="markdown", source="text")
    )
    result = orchestrator.run_full_analysis(req)

    assert result.guardrails.status == "ok"
    assert result.clarity is not None
    assert result.structure is not None
    assert result.technical is not None
    assert result.visuals is not None
    assert result.summary is not None
    assert result.tags is not None


def test_orchestrator_graceful_degradation(monkeypatch, fake_llm) -> None:
    # Force one agent to fail; overall analysis should still succeed.
    monkeypatch.setattr(orchestrator, "build_llm", lambda: fake_llm)

    def boom(*args, **kwargs):
        raise RuntimeError("agent failed")

    monkeypatch.setattr(orchestrator, "run_visual_suggestion_agent", boom)

    req = AnalysisRequest(
        document=DocumentInput(content="Hello world", content_type="markdown", source="text")
    )
    result = orchestrator.run_full_analysis(req)
    assert result.guardrails.status == "ok"
    assert result.visuals is None

