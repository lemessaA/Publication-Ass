from typing import Any, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, ClarityFeedback
from app.core.prompt_context import format_reviewer_context
from app.core.llm_parse import (
    JSON_ONLY_SUFFIX,
    clean_comment_lines,
    parse_llm_json_dict,
    truncate_plain,
)


def build_clarity_prompt(document: DocumentInput, reviewer_context: str = "") -> str:
    ctx = format_reviewer_context(reviewer_context)
    return (
        ctx
        + "You are a senior technical editor specializing in AI/ML publications.\n"
        "Rewrite the following content to maximize clarity and readability while preserving all technical meaning.\n"
        "Focus on:\n"
        "- reducing redundancy\n"
        "- simplifying complex sentences\n"
        "- keeping terminology precise\n\n"
        "Then provide 3–6 short bullet comments on major clarity improvements you made or recommend.\n\n"
        "Respond in JSON with keys 'improved_text' (string) and 'comments' (array of short strings).\n\n"
        f"CONTENT:\n{document.content}"
        + JSON_ONLY_SUFFIX
    )


def run_clarity_agent(
    llm: BaseChatModel, document: DocumentInput, reviewer_context: str = ""
) -> ClarityFeedback:
    prompt = build_clarity_prompt(document, reviewer_context)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    data: Dict[str, Any] | None = parse_llm_json_dict(content)

    if data is None:
        raw = content if isinstance(content, str) else str(content)
        return ClarityFeedback(improved_text=truncate_plain(raw, 48_000), comments=[])

    improved_text = str(data.get("improved_text") or "").strip() or document.content
    comments_raw = data.get("comments", [])
    comments_list = [str(c) for c in comments_raw if c is not None][:12]
    comments = clean_comment_lines(comments_list)[:8]
    return ClarityFeedback(improved_text=improved_text, comments=comments)
