from typing import Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, TechnicalFeedback


def build_technical_prompt(document: DocumentInput) -> str:
    return (
        "You are a senior AI/ML researcher performing a technical review of a draft publication.\n"
        "Carefully check the content for:\n"
        "- incorrect or misleading explanations\n"
        "- missing assumptions or definitions\n"
        "- unclear descriptions of models, training, data, or evaluation\n"
        "- unsubstantiated or overly strong claims\n\n"
        "Respond in JSON with keys:\n"
        "- 'issues_found': list of concrete technical issues, each a short paragraph\n"
        "- 'suggestions': list of concrete fixes or questions to resolve\n"
        "- 'overall_confidence': number between 0 and 1 expressing confidence in review\n\n"
        f"CONTENT:\n{document.content}"
    )


def run_technical_reviewer_agent(
    llm: BaseChatModel, document: DocumentInput
) -> TechnicalFeedback:
    prompt = build_technical_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    if isinstance(content, str):
        try:
            import json

            data: Dict[str, Any] = json.loads(content)
        except Exception:
            # Fallback: treat full text as one suggestion.
            return TechnicalFeedback(
                issues_found=[],
                suggestions=[content],
                overall_confidence=0.5,
            )
    elif isinstance(content, dict):
        data = content
    else:
        data = {}

    issues = [str(i) for i in data.get("issues_found", [])][:30]
    suggestions = [str(s) for s in data.get("suggestions", [])][:30]
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

