from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.api.models import (
    AnalysisRequest,
    AnalysisResponse,
    DocumentInput,
    ErrorResponse,
    HistoryItem,
    ExportFormat,
)
from app.core.orchestrator import run_full_analysis
from app.services.history_service import (
    persist_history,
    load_history_items,
    load_history_item,
)
from app.config import get_settings


router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_publication(request: AnalysisRequest) -> AnalysisResponse:
    """Main endpoint for running the multi-agent analysis."""
    try:
        settings = get_settings()
        analysis_id = str(uuid.uuid4())
        created_at = datetime.utcnow()

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
            raise HTTPException(
                status_code=400,
                detail=result.guardrails.reason or "Input rejected by guardrails.",
            )

        return response
    except HTTPException:
        # Re-raise FastAPI HTTP errors directly.
        raise
    except Exception as exc:
        # Generic error handler.
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
) -> AnalysisResponse:
    """Helper endpoint for file-based uploads."""
    try:
        raw_bytes = await file.read()
        content = raw_bytes.decode("utf-8", errors="ignore")
        document = DocumentInput(
            content=content,
            content_type=content_type,
            source="file",
            filename=file.filename,
        )
        request = AnalysisRequest(document=document)
        return await analyze_publication(request)
    except HTTPException:
        raise
    except Exception as exc:
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

