from typing import Dict, Any, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, TagFeedback


def build_tag_prompt(document: DocumentInput) -> str:
    return (
        "You are helping prepare an AI/ML paper for publication.\n"
        "1) Propose 3–8 strong, informative titles suitable for conferences or arXiv.\n"
        "2) Propose 6–15 topical tags / keywords (e.g. 'reinforcement-learning', 'vision-transformers').\n\n"
        "Respond in JSON with keys:\n"
        "- 'title_suggestions': list of strings\n"
        "- 'tags': list of strings\n\n"
        f"CONTENT:\n{document.content}"
    )


def run_tag_generator_agent(llm: BaseChatModel, document: DocumentInput) -> TagFeedback:
    prompt = build_tag_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    if isinstance(content, str):
        try:
            import json

            data: Dict[str, Any] = json.loads(content)
        except Exception:
            # Heuristic: treat each line as a potential tag/title.
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            return TagFeedback(
                title_suggestions=lines[:5],
                tags=lines[5:15],
            )
    elif isinstance(content, dict):
        data = content
    else:
        data = {}

    titles: List[str] = [str(t) for t in data.get("title_suggestions", [])][:10]
    tags: List[str] = [str(t) for t in data.get("tags", [])][:20]
    return TagFeedback(
        title_suggestions=titles,
        tags=tags,
    )

