from typing import Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, SummaryFeedback


def build_summary_prompt(document: DocumentInput) -> str:
    return (
        "You are assisting with an AI/ML publication.\n"
        "Write a concise, publication-style abstract (max ~200 words) that captures:\n"
        "- the problem being solved\n"
        "- the proposed method\n"
        "- key results or contributions\n"
        "- why it matters\n\n"
        "Then list 3–7 bullet points for the main contributions.\n\n"
        "Respond in JSON with keys 'summary' and 'key_contributions' (list of strings).\n\n"
        f"CONTENT:\n{document.content}"
    )


def run_summary_agent(llm: BaseChatModel, document: DocumentInput) -> SummaryFeedback:
    prompt = build_summary_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    if isinstance(content, str):
        try:
            import json

            data: Dict[str, Any] = json.loads(content)
        except Exception:
            return SummaryFeedback(summary=content, key_contributions=[])
    elif isinstance(content, dict):
        data = content
    else:
        data = {}

    summary = str(data.get("summary", "")).strip() or document.content[:1000]
    key_contributions = [str(c) for c in data.get("key_contributions", [])][:15]
    return SummaryFeedback(
        summary=summary,
        key_contributions=key_contributions,
    )

