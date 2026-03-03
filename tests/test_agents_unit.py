"""
Unit tests for individual agent components under `app/agents/`.

These tests verify prompt builders and the agents' ability to parse
structured outputs. They run quickly and use `fake_llm` from `conftest`.
"""

from __future__ import annotations

from app.api.models import DocumentInput
from app.agents.clarity_agent import build_clarity_prompt, run_clarity_agent
from app.agents.structure_agent import build_structure_prompt, run_structure_agent
from app.agents.technical_reviewer import build_technical_prompt, run_technical_reviewer_agent
from app.agents.visual_suggestion import build_visual_prompt, run_visual_suggestion_agent
from app.agents.summary_agent import build_summary_prompt, run_summary_agent
from app.agents.tag_generator import build_tag_prompt, run_tag_generator_agent


def test_prompts_include_document_content() -> None:
    doc = DocumentInput(content="Hello world", content_type="markdown", source="text")
    assert "Hello world" in build_clarity_prompt(doc)
    assert "Hello world" in build_structure_prompt(doc)
    assert "Hello world" in build_technical_prompt(doc)
    assert "Hello world" in build_visual_prompt(doc)
    assert "Hello world" in build_summary_prompt(doc)
    assert "Hello world" in build_tag_prompt(doc)


def test_agents_parse_structured_outputs(fake_llm) -> None:
    doc = DocumentInput(content="Hello world", content_type="markdown", source="text")

    clarity = run_clarity_agent(fake_llm, doc)
    assert clarity.improved_text
    assert clarity.comments

    structure = run_structure_agent(fake_llm, doc)
    assert structure.suggested_outline

    technical = run_technical_reviewer_agent(fake_llm, doc)
    assert technical.overall_confidence >= 0.0

    visuals = run_visual_suggestion_agent(fake_llm, doc)
    assert len(visuals.suggestions) >= 1

    summary = run_summary_agent(fake_llm, doc)
    assert summary.summary

    tags = run_tag_generator_agent(fake_llm, doc)
    assert tags.title_suggestions
    assert tags.tags


def test_agents_fallback_on_non_json(fake_llm) -> None:
    # Override mapping with non-JSON strings and ensure agents don't crash.
    fake_llm.mapping["Rewrite the following content"] = "not-json"
    doc = DocumentInput(content="Hello world", content_type="markdown", source="text")
    clarity = run_clarity_agent(fake_llm, doc)
    assert clarity.improved_text

