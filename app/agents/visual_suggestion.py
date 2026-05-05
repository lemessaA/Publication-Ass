from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, VisualFeedback, VisualSuggestion
from app.core.llm_parse import JSON_ONLY_SUFFIX, parse_llm_json_dict, split_fallback_paragraphs


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
        + JSON_ONLY_SUFFIX
    )


def run_visual_suggestion_agent(
    llm: BaseChatModel, document: DocumentInput
) -> VisualFeedback:
    prompt = build_visual_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    data = parse_llm_json_dict(content)
    raw_text = content if isinstance(content, str) else str(content)

    if data is None:
        tips = split_fallback_paragraphs(raw_text, max_items=14, max_chars_each=500)
        return VisualFeedback(
            suggestions=[],
            formatting_tips=tips,
        )

    suggestions_raw: List[Dict[str, Any]] = data.get("suggestions", []) or []
    suggestions: List[VisualSuggestion] = []
    for item in suggestions_raw[:10]:
        try:
            suggestions.append(
                VisualSuggestion(
                    title=str(item.get("title", "Figure")).strip() or "Figure",
                    description=str(item.get("description", "")).strip(),
                    type=str(item.get("type", "diagram")).strip() or "diagram",
                )
            )
        except Exception:
            continue

    formatting_tips = [
        str(t).strip() for t in data.get("formatting_tips", []) if str(t).strip()
    ][:20]
    return VisualFeedback(
        suggestions=suggestions,
        formatting_tips=formatting_tips,
    )
