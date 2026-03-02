from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class ContentType(str, Enum):
    plain_text = "plain_text"
    markdown = "markdown"
    latex = "latex"


class InputSource(str, Enum):
    text = "text"
    file = "file"


class DocumentInput(BaseModel):
    """User-provided document for analysis."""

    content: str = Field(..., description="Raw text of the document.")
    content_type: ContentType = Field(
        default=ContentType.markdown,
        description="Format of the content. Used for formatting suggestions.",
    )
    source: InputSource = Field(
        default=InputSource.text,
        description="How the content was provided.",
    )
    filename: Optional[str] = Field(
        default=None,
        description="Optional filename when uploaded from a file.",
    )

    @field_validator("content")
    @classmethod
    def strip_and_require(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Document content cannot be empty.")
        return v


class ClarityFeedback(BaseModel):
    improved_text: str
    comments: List[str] = Field(default_factory=list)


class StructureFeedback(BaseModel):
    suggested_outline: List[str] = Field(
        default_factory=list,
        description="High-level ordered outline sections.",
    )
    section_suggestions: List[str] = Field(
        default_factory=list,
        description="Comments on how to reorganize sections.",
    )


class TechnicalFeedback(BaseModel):
    issues_found: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How confident the model is in its technical review.",
    )


class VisualSuggestion(BaseModel):
    title: str
    description: str
    type: str = Field(
        description="Diagram / table / figure / equation / code-block / other.",
    )


class VisualFeedback(BaseModel):
    suggestions: List[VisualSuggestion] = Field(default_factory=list)
    formatting_tips: List[str] = Field(default_factory=list)


class SummaryFeedback(BaseModel):
    summary: str
    key_contributions: List[str] = Field(default_factory=list)


class TagFeedback(BaseModel):
    title_suggestions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class GuardrailStatus(str, Enum):
    ok = "ok"
    rejected = "rejected"


class GuardrailResult(BaseModel):
    status: GuardrailStatus
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AnalysisResult(BaseModel):
    clarity: Optional[ClarityFeedback] = None
    structure: Optional[StructureFeedback] = None
    technical: Optional[TechnicalFeedback] = None
    visuals: Optional[VisualFeedback] = None
    summary: Optional[SummaryFeedback] = None
    tags: Optional[TagFeedback] = None
    guardrails: GuardrailResult = Field(
        default_factory=lambda: GuardrailResult(status=GuardrailStatus.ok)
    )


class AnalysisRequest(BaseModel):
    document: DocumentInput
    # Flags to selectively enable agents if needed in the future.
    run_clarity: bool = True
    run_structure: bool = True
    run_technical: bool = True
    run_visuals: bool = True
    run_summary: bool = True
    run_tags: bool = True


class AnalysisResponse(BaseModel):
    id: str
    created_at: datetime
    request: AnalysisRequest
    result: AnalysisResult


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HistoryItem(BaseModel):
    id: str
    created_at: datetime
    request: AnalysisRequest
    result: AnalysisResult


class ExportFormat(str, Enum):
    json = "json"

