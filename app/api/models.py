from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator


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


class SectionScope(BaseModel):
    """1-based inclusive line range over ``document.content`` (``splitlines()`` semantics)."""

    start_line: int = Field(ge=1, description="First line to include (1-based).")
    end_line: int = Field(ge=1, description="Last line to include (1-based).")

    @model_validator(mode="after")
    def end_after_start(self) -> SectionScope:
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line.")
        return self


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
    analysis_warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal notices for the client (e.g. document truncated for LLM).",
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
    section_scope: Optional[SectionScope] = Field(
        default=None,
        description="If set, only this line range is sent to reviewers and the LLM (after sanitization).",
    )
    section_hint: Optional[str] = Field(
        default=None,
        description="Optional note for reviewers (e.g. section title). Shown in addition to persona.",
    )
    redact_before_llm: bool = Field(
        default=False,
        description="If true, replace email/phone/grant-like strings before sending text to the LLM.",
    )

    @model_validator(mode="after")
    def section_scope_fits_document(self) -> AnalysisRequest:
        if self.section_scope is None:
            return self
        from app.core.section_extract import slice_document_for_section_analysis

        try:
            slice_document_for_section_analysis(self.document.content, self.section_scope)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return self


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

