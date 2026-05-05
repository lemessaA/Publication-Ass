import re
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, TagFeedback
from app.core.llm_parse import JSON_ONLY_SUFFIX, parse_llm_json_dict, truncate_plain


def build_tag_prompt(document: DocumentInput) -> str:
    return (
        "You are helping prepare an AI/ML paper for publication.\n"
        "1) Propose 3–8 strong, informative titles suitable for conferences or arXiv.\n"
        "2) Propose 6–15 topical tags / keywords (e.g. 'reinforcement-learning', 'vision-transformers').\n\n"
        "Respond in JSON with keys:\n"
        "- 'title_suggestions': list of strings\n"
        "- 'tags': list of strings\n\n"
        f"CONTENT:\n{document.content}"
        + JSON_ONLY_SUFFIX
    )


def _split_fallback_tag_lines(content: str) -> tuple[list[str], list[str]]:
    lines = []
    for ln in content.splitlines():
        t = re.sub(r"^\s*[-*•]\s*", "", ln.strip())
        if not t or t.startswith("```"):
            continue
        if len(t) > 180:
            t = truncate_plain(t, 180)
        lines.append(t)
    lines = lines[:20]
    titles = lines[:6]
    tags = lines[6:18]
    return titles, tags


def run_tag_generator_agent(llm: BaseChatModel, document: DocumentInput) -> TagFeedback:
    prompt = build_tag_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    data = parse_llm_json_dict(content)
    raw_text = content if isinstance(content, str) else str(content)

    if data is None:
        titles, tags = _split_fallback_tag_lines(raw_text)
        return TagFeedback(title_suggestions=titles, tags=tags)

    titles = [str(t).strip() for t in data.get("title_suggestions", []) if str(t).strip()][:10]
    tags = [str(t).strip() for t in data.get("tags", []) if str(t).strip()][:20]
    return TagFeedback(
        title_suggestions=titles,
        tags=tags,
    )
