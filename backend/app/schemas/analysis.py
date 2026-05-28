from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SummaryMode = Literal["extractive", "abstractive", "bullet"]
SummaryLength = Literal["short", "medium", "long"]
SummarySource = Literal["pdf", "docx"]
ExportFormat = Literal["txt", "docx"]


class SummaryRequest(BaseModel):
    source_type: SummarySource = "pdf"
    mode: SummaryMode = "extractive"
    length: SummaryLength = "medium"
    language_hint: str = "auto"


class SummaryResponse(BaseModel):
    job_id: str
    source_type: SummarySource
    mode: SummaryMode
    length: SummaryLength
    summary_text: str
    bullets: list[str] = Field(default_factory=list)
    language: str = "auto"
    model_used: str
    used_fallback: bool = False


class InsightResponse(BaseModel):
    job_id: str
    source_type: SummarySource
    keywords: list[str]
    topics: list[str]
    sentiment_label: str
    sentiment_score: float
    classification_label: str
    classification_score: float
    generated_at: datetime
    model_used: str
    used_fallback: bool = False


class DashboardStatsResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    queued_jobs: int
    total_pages_processed: int
    average_output_size_bytes: float
    latest_job_filename: str | None = None
