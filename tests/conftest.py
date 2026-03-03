"""
Shared test fixtures and helpers used across the test suite.

- Provides `fake_llm`: a lightweight, deterministic LLM stub used to
    exercise agents and orchestrator flows without external network calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pytest


@dataclass
class FakeResponse:
    content: Any


class FakeLLM:
    """Simple duck-typed LLM stub used in tests."""

    def __init__(self, mapping: Dict[str, Any]):
        self.mapping = mapping

    def invoke(self, messages):
        text = ""
        if messages:
            msg = messages[0]
            text = getattr(msg, "content", "") or ""

        for key, value in self.mapping.items():
            if key in text:
                return FakeResponse(content=value)
        return FakeResponse(content={})


@pytest.fixture
def fake_llm():
    return FakeLLM(
        mapping={
            "Rewrite the following content": {
                "improved_text": "Improved.",
                "comments": ["Comment 1"],
            },
            "propose an improved logical structure": {
                "suggested_outline": ["Intro", "Method", "Results"],
                "section_suggestions": ["Rename section 2"],
            },
            "performing a technical review": {
                "issues_found": ["Issue 1"],
                "suggestions": ["Suggestion 1"],
                "overall_confidence": 0.7,
            },
            "visualization and formatting expert": {
                "suggestions": [
                    {"title": "Ablation table", "description": "Show ablations", "type": "table"}
                ],
                "formatting_tips": ["Use consistent headings"],
            },
            "Write a concise, publication-style abstract": {
                "summary": "Abstract.",
                "key_contributions": ["Contribution 1"],
            },
            "Propose 3–8 strong, informative titles": {
                "title_suggestions": ["Title 1"],
                "tags": ["tag1", "tag2"],
            },
        }
    )

