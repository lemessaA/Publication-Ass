from __future__ import annotations

import logging
from typing import Any, Iterator, TypedDict

from langgraph.graph import StateGraph, END 

from app.api.models import (
    AnalysisRequest,
    AnalysisResult,
    ClarityFeedback,
    StructureFeedback,
    TechnicalFeedback,
    VisualFeedback,
    SummaryFeedback,
    TagFeedback,
    GuardrailResult,
)
from app.agents.clarity_agent import run_clarity_agent
from app.agents.structure_agent import run_structure_agent
from app.agents.technical_reviewer import run_technical_reviewer_agent
from app.agents.visual_suggestion import run_visual_suggestion_agent
from app.agents.summary_agent import run_summary_agent
from app.agents.tag_generator import run_tag_generator_agent
from app.config import get_settings
from app.core.document_window import window_document_for_llm
from app.core.guardrails import apply_guardrails
from app.core.retry import call_with_retries
from app.core.safety import filter_analysis_result
from app.services.llm_service import build_llm

logger = logging.getLogger(__name__)


class OrchestratorState(TypedDict, total=False):
    """Shared state that flows through the LangGraph execution.

    Each key is written by at most one node per step to avoid
    INVALID_CONCURRENT_GRAPH_UPDATE errors.
    """

    request: AnalysisRequest
    reviewer_context: str
    guardrails: GuardrailResult
    clarity: ClarityFeedback
    structure: StructureFeedback
    technical: TechnicalFeedback
    visuals: VisualFeedback
    summary: SummaryFeedback
    tags: TagFeedback


def supervisor_node(state: OrchestratorState) -> OrchestratorState:
    """Supervisor performs guardrail checks."""
    request = state["request"]
    guardrail_result = apply_guardrails(request)
    # Only return the keys we modify; LangGraph will merge them
    return {"guardrails": guardrail_result}


def clarity_node(state: OrchestratorState) -> OrchestratorState:
    if not state["request"].run_clarity:
        return {}
    ctx = state.get("reviewer_context") or ""

    def _call():
        llm = build_llm()
        return run_clarity_agent(llm, state["request"].document, ctx)

    clarity = call_with_retries(_call, description="clarity_agent")
    if clarity is None:
        logger.error("Clarity agent failed after retries")
        return {}
    return {"clarity": clarity}


def structure_node(state: OrchestratorState) -> OrchestratorState:
    if not state["request"].run_structure:
        return {}
    ctx = state.get("reviewer_context") or ""

    def _call():
        llm = build_llm()
        return run_structure_agent(llm, state["request"].document, ctx)

    structure = call_with_retries(_call, description="structure_agent")
    if structure is None:
        logger.error("Structure agent failed after retries")
        return {}
    return {"structure": structure}


def technical_node(state: OrchestratorState) -> OrchestratorState:
    if not state["request"].run_technical:
        return {}
    ctx = state.get("reviewer_context") or ""

    def _call():
        llm = build_llm()
        return run_technical_reviewer_agent(llm, state["request"].document, ctx)

    technical = call_with_retries(_call, description="technical_reviewer_agent")
    if technical is None:
        logger.error("Technical reviewer agent failed after retries")
        return {}
    return {"technical": technical}


def visuals_node(state: OrchestratorState) -> OrchestratorState:
    if not state["request"].run_visuals:
        return {}
    ctx = state.get("reviewer_context") or ""

    def _call():
        llm = build_llm()
        return run_visual_suggestion_agent(llm, state["request"].document, ctx)

    visuals = call_with_retries(_call, description="visual_suggestion_agent")
    if visuals is None:
        logger.error("Visual suggestion agent failed after retries")
        return {}
    return {"visuals": visuals}


def summary_node(state: OrchestratorState) -> OrchestratorState:
    if not state["request"].run_summary:
        return {}
    ctx = state.get("reviewer_context") or ""

    def _call():
        llm = build_llm()
        return run_summary_agent(llm, state["request"].document, ctx)

    summary = call_with_retries(_call, description="summary_agent")
    if summary is None:
        logger.error("Summary agent failed after retries")
        return {}
    return {"summary": summary}


def tags_node(state: OrchestratorState) -> OrchestratorState:
    if not state["request"].run_tags:
        return {}
    ctx = state.get("reviewer_context") or ""

    def _call():
        llm = build_llm()
        return run_tag_generator_agent(llm, state["request"].document, ctx)

    tags = call_with_retries(_call, description="tag_generator_agent")
    if tags is None:
        logger.error("Tag generator agent failed after retries")
        return {}
    return {"tags": tags}


def build_graph():
    """Build the LangGraph orchestration graph."""
    graph = StateGraph(OrchestratorState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("clarity", clarity_node)
    graph.add_node("structure", structure_node)
    graph.add_node("technical", technical_node)
    graph.add_node("visuals", visuals_node)
    graph.add_node("summary", summary_node)
    graph.add_node("tags", tags_node)

    # Execution order: supervisor -> all agents in parallel -> END.
    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "clarity")
    graph.add_edge("supervisor", "structure")
    graph.add_edge("supervisor", "technical")
    graph.add_edge("supervisor", "visuals")
    graph.add_edge("supervisor", "summary")
    graph.add_edge("supervisor", "tags")

    graph.add_edge("clarity", END)
    graph.add_edge("structure", END)
    graph.add_edge("technical", END)
    graph.add_edge("visuals", END)
    graph.add_edge("summary", END)
    graph.add_edge("tags", END)

    return graph.compile()


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def prepare_orchestrator_state(request: AnalysisRequest) -> tuple[OrchestratorState, list[str]]:
    """Window document text for LLM limits and build initial LangGraph state."""
    settings = get_settings()
    req_llm = request.model_copy(deep=True)
    new_content, truncated = window_document_for_llm(
        req_llm.document.content,
        settings.max_llm_input_chars,
    )
    req_llm.document.content = new_content

    warnings: list[str] = []
    if truncated:
        warnings.append(
            "Document was shortened for the language model context limit "
            f"({settings.max_llm_input_chars:,} characters). "
            "Paste a shorter excerpt or set MAX_LLM_INPUT_CHARS higher if your Groq tier allows larger prompts."
        )
        logger.info(
            "document_windowed_for_llm original_len=%s windowed_len=%s max_llm_input_chars=%s",
            len(request.document.content),
            len(new_content),
            settings.max_llm_input_chars,
        )

    initial_state: OrchestratorState = {
        "request": req_llm,
        "reviewer_context": settings.reviewer_persona,
    }
    return initial_state, warnings


def run_full_analysis(request: AnalysisRequest) -> AnalysisResult:
    """Execute the LangGraph pipeline to produce an AnalysisResult."""
    initial_state, warnings = prepare_orchestrator_state(request)
    graph = get_graph()
    final_state = graph.invoke(initial_state)

    result = AnalysisResult(
        clarity=final_state.get("clarity"),
        structure=final_state.get("structure"),
        technical=final_state.get("technical"),
        visuals=final_state.get("visuals"),
        summary=final_state.get("summary"),
        tags=final_state.get("tags"),
        guardrails=final_state["guardrails"],
        analysis_warnings=warnings,
    )
    return filter_analysis_result(result)


def iter_analysis_stream_events(request: AnalysisRequest) -> Iterator[dict[str, Any]]:
    """Yield per-node completion events, then a final ``done`` event with the result.

    Uses LangGraph ``stream_mode=\"updates\"`` so parallel agents report completions
    in completion order (not a fixed pipeline order).
    """
    initial_state, warnings = prepare_orchestrator_state(request)
    graph = get_graph()
    acc: dict[str, Any] = dict(initial_state)

    for chunk in graph.stream(initial_state, stream_mode="updates"):
        for node_name, update in chunk.items():
            yield {"type": "step", "step": node_name}
            if update is not None:
                acc.update(update)

    if "guardrails" not in acc:
        raise RuntimeError("Supervisor did not set guardrails state.")

    result = AnalysisResult(
        clarity=acc.get("clarity"),
        structure=acc.get("structure"),
        technical=acc.get("technical"),
        visuals=acc.get("visuals"),
        summary=acc.get("summary"),
        tags=acc.get("tags"),
        guardrails=acc["guardrails"],
        analysis_warnings=warnings,
    )
    yield {"type": "done", "result": filter_analysis_result(result)}

