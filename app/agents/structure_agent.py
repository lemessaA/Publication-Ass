from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.api.models import DocumentInput, StructureFeedback
from app.core.llm_parse import JSON_ONLY_SUFFIX, parse_llm_json_dict


def build_structure_prompt(document: DocumentInput) -> str:
    return (
        "You are an expert in scientific writing and conference paper structure.\n"
        "Analyze the following AI/ML document and propose an improved logical structure.\n"
        "1) Provide an ordered list of high-level sections for an ideal outline.\n"
        "2) Provide 3–8 concrete suggestions on how to reorganize or rename sections.\n\n"
        "Respond in JSON with keys 'suggested_outline' (list of strings) and "
        "'section_suggestions' (list of strings).\n\n"
        f"CONTENT:\n{document.content}"
        + JSON_ONLY_SUFFIX
    )


def run_structure_agent(llm: BaseChatModel, document: DocumentInput) -> StructureFeedback:
    prompt = build_structure_prompt(document)
    message = HumanMessage(content=prompt)
    response = llm.invoke([message])

    content = response.content
    data = parse_llm_json_dict(content)

    if data is None:
        lines = [line.strip() for line in document.content.splitlines()]
        outline = [line for line in lines if line.startswith("#")]
        return StructureFeedback(suggested_outline=outline[:40], section_suggestions=[])

    outline = [str(s).strip() for s in data.get("suggested_outline", []) if str(s).strip()][:30]
    section_suggestions = [
        str(s).strip() for s in data.get("section_suggestions", []) if str(s).strip()
    ][:30]
    return StructureFeedback(
        suggested_outline=outline,
        section_suggestions=section_suggestions,
    )
