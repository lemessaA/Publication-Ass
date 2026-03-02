from typing import Dict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, StructureFeedback


def build_structure_prompt(document: DocumentInput) -> str:
    return (
        "You are an expert in scientific writing and conference paper structure.\n"
        "Analyze the following AI/ML document and propose an improved logical structure.\n"
        "1) Provide an ordered list of high-level sections for an ideal outline.\n"
        "2) Provide 3–8 concrete suggestions on how to reorganize or rename sections.\n\n"
        "Respond in JSON with keys 'suggested_outline' (list of strings) and "
        "'section_suggestions' (list of strings).\n\n"
        f"CONTENT:\n{document.content}"
    )


def run_structure_agent(llm: BaseChatModel, document: DocumentInput) -> StructureFeedback:
    prompt = build_structure_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    if isinstance(content, str):
        try:
            import json

            data: Dict[str, Any] = json.loads(content)
        except Exception:
            # Fallback: simple heuristic outline using headings.
            lines = [line.strip() for line in document.content.splitlines()]
            outline = [line for line in lines if line.startswith("#")]
            return StructureFeedback(suggested_outline=outline, section_suggestions=[])
    elif isinstance(content, dict):
        data = content
    else:
        data = {}

    outline = [str(s) for s in data.get("suggested_outline", [])][:30]
    section_suggestions = [str(s) for s in data.get("section_suggestions", [])][:30]
    return StructureFeedback(
        suggested_outline=outline,
        section_suggestions=section_suggestions,
    )

