from app.api.models import DocumentInput
from app.agents.clarity_agent import build_clarity_prompt


def test_build_clarity_prompt_includes_content() -> None:
    doc = DocumentInput(content="Test content", content_type="markdown", source="text")
    prompt = build_clarity_prompt(doc)
    assert "Test content" in prompt

