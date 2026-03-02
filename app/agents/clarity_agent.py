from typing import Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, ClarityFeedback


def build_clarity_prompt(document: DocumentInput) -> str:
    return (
        "You are a senior technical editor specializing in AI/ML publications.\n"
        "Rewrite the following content to maximize clarity and readability while preserving all technical meaning.\n"
        "Focus on:\n"
        "- reducing redundancy\n"
        "- simplifying complex sentences\n"
        "- keeping terminology precise\n\n"
        "Then provide 3–6 short bullet comments on major clarity improvements you made or recommend.\n\n"
        "Respond in JSON with keys 'improved_text' and 'comments'.\n\n"
        f"CONTENT:\n{document.content}"
    )


def run_clarity_agent(llm: BaseChatModel, document: DocumentInput) -> ClarityFeedback:
    """Run the clarity agent using the provided LLM."""
    prompt = build_clarity_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    # We ask the model for JSON; be defensive in case format drifts.
    content = response.content
    if isinstance(content, str):
        try:
            import json

            data: Dict[str, Any] = json.loads(content)
        except Exception:
            # Fallback: treat full text as improved_text.
            return ClarityFeedback(improved_text=content, comments=[])
    elif isinstance(content, dict):
        data = content
    else:
        # Fallback if model returns a list or other structure.
        data = {"improved_text": str(content), "comments": []}

    improved_text = data.get("improved_text") or document.content
    comments_raw = data.get("comments", [])
    comments = [str(c) for c in comments_raw][:10]
    return ClarityFeedback(improved_text=improved_text, comments=comments)

