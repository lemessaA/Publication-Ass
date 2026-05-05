from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, SummaryFeedback
from app.core.llm_parse import JSON_ONLY_SUFFIX, parse_llm_json_dict, truncate_plain


def build_summary_prompt(document: DocumentInput) -> str:
    return (
        "You are assisting with an AI/ML publication.\n"
        "Write a concise, publication-style abstract (max ~200 words) that captures:\n"
        "- the problem being solved\n"
        "- the proposed method\n"
        "- key results or contributions\n"
        "- why it matters\n\n"
        "Then list 3–7 bullet points for the main contributions.\n\n"
        "Respond in JSON with keys 'summary' (string) and 'key_contributions' (list of strings).\n\n"
        f"CONTENT:\n{document.content}"
        + JSON_ONLY_SUFFIX
    )


def run_summary_agent(llm: BaseChatModel, document: DocumentInput) -> SummaryFeedback:
    prompt = build_summary_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    data = parse_llm_json_dict(content)
    raw_text = content if isinstance(content, str) else str(content)

    if data is None:
        return SummaryFeedback(
            summary=truncate_plain(raw_text, 3_500),
            key_contributions=[],
        )

    summary = str(data.get("summary", "")).strip()
    if not summary:
        summary = truncate_plain(document.content, 2_000)

    key_contributions = [
        str(c).strip() for c in data.get("key_contributions", []) if str(c).strip()
    ][:15]
    return SummaryFeedback(
        summary=summary,
        key_contributions=key_contributions,
    )
