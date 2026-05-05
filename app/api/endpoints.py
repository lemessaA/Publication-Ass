from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Iterator, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.models import (
    AnalysisRequest,
    AnalysisResponse,
    DocumentInput,
    ErrorResponse,
    HistoryItem,
    ExportFormat,
    SectionScope,
)
from app.core.orchestrator import iter_analysis_stream_events, run_full_analysis
from app.core.safety import sanitize_input_text
from app.services.history_service import (
    persist_history,
    load_history_items,
    load_history_item,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _analysis_request_from_upload(
    document: DocumentInput,
    *,
    section_hint: str | None,
    section_start_line: int | None,
    section_end_line: int | None,
    redact_before_llm: bool = False,
) -> AnalysisRequest:
    """Build ``AnalysisRequest`` with optional section scope (multipart form fields)."""
    scope: SectionScope | None = None
    if section_start_line is not None or section_end_line is not None:
        if section_start_line is None or section_end_line is None:
            raise HTTPException(
                status_code=400,
                detail="Provide both section_start_line and section_end_line for section-scoped analysis.",
            )
        scope = SectionScope(start_line=section_start_line, end_line=section_end_line)
    hint = (section_hint or "").strip() or None
    return AnalysisRequest(
        document=document,
        section_scope=scope,
        section_hint=hint,
        redact_before_llm=redact_before_llm,
    )


def _format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _analysis_sse_events(
    *, analysis_id: str, created_at: datetime, request: AnalysisRequest
) -> Iterator[str]:
    yield _format_sse(
        {
            "type": "start",
            "id": analysis_id,
            "created_at": created_at.isoformat(),
        }
    )
    for event in iter_analysis_stream_events(request):
        if event["type"] == "step":
            yield _format_sse({"type": "step", "step": event["step"]})
        elif event["type"] == "done":
            result = event["result"]
            response = AnalysisResponse(
                id=analysis_id,
                created_at=created_at,
                request=request,
                result=result,
            )
            settings = get_settings()
            if settings.history_backend == "file" and result.guardrails.status == "ok":
                persist_history(
                    HistoryItem(
                        id=response.id,
                        created_at=response.created_at,
                        request=response.request,
                        result=response.result,
                    )
                )
            yield _format_sse(
                {
                    "type": "complete",
                    "response": response.model_dump(mode="json"),
                }
            )
        else:
            logger.warning("unknown_stream_event type=%s", event.get("type"))


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_publication(request: AnalysisRequest) -> AnalysisResponse:
    """Main endpoint for running the multi-agent analysis."""
    analysis_id = str(uuid.uuid4())
    try:
        settings = get_settings()
        created_at = datetime.utcnow()

        # Minimal sanitization (Pydantic still does full validation).
        request.document.content = sanitize_input_text(request.document.content)

        logger.info(
            "analysis_started id=%s content_len=%s source=%s content_type=%s",
            analysis_id,
            len(request.document.content),
            request.document.source,
            request.document.content_type,
        )

        result = run_full_analysis(request)

        response = AnalysisResponse(
            id=analysis_id,
            created_at=created_at,
            request=request,
            result=result,
        )

        # Optionally persist to history.
        if settings.history_backend == "file":
            persist_history(
                HistoryItem(
                    id=response.id,
                    created_at=response.created_at,
                    request=response.request,
                    result=response.result,
                )
            )

        # If guardrails rejected content, surface as 400 even though we return the structure.
        if result.guardrails.status != "ok":
            logger.warning(
                "analysis_rejected id=%s reason=%s", analysis_id, result.guardrails.reason
            )
            raise HTTPException(
                status_code=400,
                detail=result.guardrails.reason or "Input rejected by guardrails.",
            )

        logger.info("analysis_completed id=%s", analysis_id)
        return response
    except HTTPException:
        # Re-raise FastAPI HTTP errors directly.
        raise
    except Exception as exc:
        logger.exception("analysis_failed id=%s", analysis_id)
        # Generic error handler.
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze document: {exc}",
        ) from exc


@router.post(
    "/analyze/stream",
    responses={500: {"model": ErrorResponse}},
)
async def analyze_publication_stream(request: AnalysisRequest) -> StreamingResponse:
    """Run analysis and stream Server-Sent Events with per-node progress."""
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    try:
        request.document.content = sanitize_input_text(request.document.content)
        logger.info(
            "analysis_stream_started id=%s content_len=%s source=%s content_type=%s",
            analysis_id,
            len(request.document.content),
            request.document.source,
            request.document.content_type,
        )
        return StreamingResponse(
            _analysis_sse_events(
                analysis_id=analysis_id, created_at=created_at, request=request
            ),
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as exc:
        logger.exception("analysis_stream_failed id=%s", analysis_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze document: {exc}",
        ) from exc


@router.post(
    "/analyze/file",
    response_model=AnalysisResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_file(
    file: UploadFile = File(...),
    content_type: str = Form("markdown"),
    section_hint: str | None = Form(None),
    section_start_line: int | None = Form(None),
    section_end_line: int | None = Form(None),
    redact_before_llm: bool = Form(False),
) -> AnalysisResponse:
    """Helper endpoint for file-based uploads."""
    try:
        # Avoid unbounded uploads.
        raw_bytes = await file.read()
        if len(raw_bytes) > 5_000_000:
            raise HTTPException(status_code=400, detail="Uploaded file is too large.")

        content = sanitize_input_text(raw_bytes.decode("utf-8", errors="ignore"))
        document = DocumentInput(
            content=content,
            content_type=content_type,
            source="file",
            filename=file.filename,
        )
        request = _analysis_request_from_upload(
            document,
            section_hint=section_hint,
            section_start_line=section_start_line,
            section_end_line=section_end_line,
        )
        return await analyze_publication(request)
    except HTTPException:
        raise
    except ValueError as exc:
        # Pydantic validators can raise ValueError; return as 400 instead of 500.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("analysis_file_failed filename=%s", file.filename)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze uploaded file: {exc}",
        ) from exc


@router.post(
    "/analyze/file/stream",
    responses={500: {"model": ErrorResponse}},
)
async def analyze_file_stream(
    file: UploadFile = File(...),
    content_type: str = Form("markdown"),
    section_hint: str | None = Form(None),
    section_start_line: int | None = Form(None),
    section_end_line: int | None = Form(None),
) -> StreamingResponse:
    """Stream SSE analysis for an uploaded file."""
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    try:
        raw_bytes = await file.read()
        if len(raw_bytes) > 5_000_000:
            raise HTTPException(status_code=400, detail="Uploaded file is too large.")

        content = sanitize_input_text(raw_bytes.decode("utf-8", errors="ignore"))
        document = DocumentInput(
            content=content,
            content_type=content_type,
            source="file",
            filename=file.filename,
        )
        request = _analysis_request_from_upload(
            document,
            section_hint=section_hint,
            section_start_line=section_start_line,
            section_end_line=section_end_line,
        )

        logger.info(
            "analysis_file_stream_started id=%s filename=%s content_len=%s",
            analysis_id,
            file.filename,
            len(request.document.content),
        )

        return StreamingResponse(
            _analysis_sse_events(
                analysis_id=analysis_id, created_at=created_at, request=request
            ),
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("analysis_file_stream_failed filename=%s", file.filename)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze uploaded file: {exc}",
        ) from exc


@router.get(
    "/history",
    response_model=List[HistoryItem],
    responses={500: {"model": ErrorResponse}},
)
async def list_history() -> List[HistoryItem]:
    """Return previous analyses (if file-based history is enabled)."""
    try:
        return load_history_items()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load history: {exc}",
        ) from exc


@router.get(
    "/history/{item_id}",
    response_model=HistoryItem,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_history_item(item_id: str) -> HistoryItem:
    settings = get_settings()
    if settings.history_backend != "file":
        raise HTTPException(status_code=404, detail="History is not enabled.")
    try:
        item = load_history_item(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="History item not found.")
        return item
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load history item: {exc}",
        ) from exc


@router.get(
    "/history/{item_id}/export",
    responses={200: {"content": {"application/json": {}}}, 404: {"model": ErrorResponse}},
)
async def export_history_item(
    item_id: str,
    fmt: ExportFormat = ExportFormat.json,
):
    """Export a history item (currently only JSON)."""
    if fmt != ExportFormat.json:
        raise HTTPException(status_code=400, detail="Unsupported export format.")

    item = await get_history_item(item_id)
    payload = item.model_dump(mode="json")
    return JSONResponse(
        content=payload,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{item_id}.json"'
        },
    )

