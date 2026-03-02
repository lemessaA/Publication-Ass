from typing import Dict, Any, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, VisualFeedback, VisualSuggestion


def build_visual_prompt(document: DocumentInput) -> str:
    return (
        "You are a visualization and formatting expert for AI/ML publications.\n"
        "Analyze the document and suggest:\n"
        "1) 3–8 concrete diagrams / figures / tables that would strengthen the paper, including a short title, type, and when to place them.\n"
        "2) 5–10 specific formatting tips for the current content style "
        "(e.g., headings, equations, code blocks, bullet lists).\n\n"
        "Respond in JSON with keys:\n"
        "- 'suggestions': list of objects { 'title', 'description', 'type' }\n"
        "- 'formatting_tips': list of strings\n\n"
        f"CONTENT:\n{document.content}"
    )


def run_visual_suggestion_agent(
    llm: BaseChatModel, document: DocumentInput
) -> VisualFeedback:
    prompt = build_visual_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    if isinstance(content, str):
        try:
            import json

            data: Dict[str, Any] = json.loads(content)
        except Exception:
            return VisualFeedback(
                suggestions=[],
                formatting_tips=[content],
            )
    elif isinstance(content, dict):
        data = content
    else:
        data = {}

    suggestions_raw: List[Dict[str, Any]] = data.get("suggestions", []) or []
    suggestions: List[VisualSuggestion] = []
    for item in suggestions_raw[:10]:
        try:
            suggestions.append(
                VisualSuggestion(
                    title=str(item.get("title", "Untitled visual suggestion")),
                    description=str(item.get("description", "")),
                    type=str(item.get("type", "diagram")),
                )
            )
        except Exception:
            continue

    formatting_tips = [str(t) for t in data.get("formatting_tips", [])][:20]
    return VisualFeedback(
        suggestions=suggestions,
        formatting_tips=formatting_tips,
    )

