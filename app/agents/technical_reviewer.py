from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, TechnicalFeedback
from app.core.prompt_context import format_reviewer_context
from app.core.llm_parse import JSON_ONLY_SUFFIX, parse_llm_json_dict, split_fallback_paragraphs


def build_technical_prompt(document: DocumentInput, reviewer_context: str = "") -> str:
    ctx = format_reviewer_context(reviewer_context)
    return (
        ctx
        + "You are a senior AI/ML researcher performing a technical review of a draft publication.\n"
        "Carefully check the content for:\n"
        "- incorrect or misleading explanations\n"
        "- missing assumptions or definitions\n"
        "- unclear descriptions of models, training, data, or evaluation\n"
        "- unsubstantiated or overly strong claims\n\n"
        "Respond in JSON with keys:\n"
        "- 'issues_found': list of concrete technical issues (each item one focused paragraph)\n"
        "- 'suggestions': list of concrete fixes or questions to resolve\n"
        "- 'overall_confidence': number between 0 and 1 expressing confidence in review\n\n"
        f"CONTENT:\n{document.content}"
        + JSON_ONLY_SUFFIX
    )


def run_technical_reviewer_agent(
    llm: BaseChatModel, document: DocumentInput, reviewer_context: str = ""
) -> TechnicalFeedback:
    prompt = build_technical_prompt(document, reviewer_context)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    data = parse_llm_json_dict(content)

    raw_text = content if isinstance(content, str) else str(content)

    if data is None:
        chunks = split_fallback_paragraphs(raw_text, max_items=10, max_chars_each=900)
        return TechnicalFeedback(
            issues_found=[],
            suggestions=chunks,
            overall_confidence=0.45,
        )

    issues = [str(i).strip() for i in data.get("issues_found", []) if str(i).strip()][:30]
    suggestions = [str(s).strip() for s in data.get("suggestions", []) if str(s).strip()][:30]
    try:
        confidence = float(data.get("overall_confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    return TechnicalFeedback(
        issues_found=issues,
        suggestions=suggestions,
        overall_confidence=confidence,
    )
