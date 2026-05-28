from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class JobState(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    EXTRACTING = "extracting"
    OCR = "ocr"
    BUILDING = "building"
    PREVIEWING = "previewing"
    COMPLETED = "completed"
    FAILED = "failed"


class SpanStyle(BaseModel):
    font_name: str = "Calibri"
    font_size: float = 11.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str | None = None


class TextSpan(BaseModel):
    text: str
    bbox: list[float]
    style: SpanStyle


class ParagraphBlock(BaseModel):
    kind: Literal["paragraph", "list"] = "paragraph"
    bbox: list[float]
    spans: list[TextSpan]
    alignment: Literal["left", "center", "right", "justify"] = "left"
    line_spacing: float = 1.0
    left_indent: float = 0.0
    first_line_indent: float = 0.0
    space_before: float = 0.0
    space_after: float = 0.0
    list_level: int = 0
    list_type: Literal["bullet", "number", "none"] = "none"


class TableCellLayout(BaseModel):
    text: str = ""
    row_span: int = 1
    col_span: int = 1
    bold: bool = False
    italic: bool = False
    align: Literal["left", "center", "right"] = "left"


class TableBlock(BaseModel):
    kind: Literal["table"] = "table"
    bbox: list[float]
    rows: list[list[TableCellLayout]]
    border: bool = True


class ImageBlock(BaseModel):
    kind: Literal["image"] = "image"
    bbox: list[float]
    image_path: str
    width_px: int
    height_px: int


class PageLayout(BaseModel):
    page_number: int
    width: float
    height: float
    rotation: int = 0
    columns: int = 1
    margins: dict[str, float] = Field(default_factory=lambda: {"top": 36, "bottom": 36, "left": 36, "right": 36})
    header_text: str = ""
    footer_text: str = ""
    blocks: list[ParagraphBlock | TableBlock | ImageBlock] = Field(default_factory=list)


class PdfAnalysis(BaseModel):
    file_name: str
    page_count: int
    mode: Literal["text", "scanned", "mixed"]
    languages: str
    has_rotated_pages: bool = False
    has_columns: bool = False
    has_tables: bool = False
    has_images: bool = False
    pages: list[PageLayout] = Field(default_factory=list)


class JobCreateResponse(BaseModel):
    job_id: str
    filename: str
    status: JobState


class JobProgressResponse(BaseModel):
    job_id: str
    filename: str
    status: JobState
    progress: int
    stage_message: str
    mode: str | None = None
    error_message: str | None = None
    download_url: str | None = None
    preview_url: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class BatchJobCreateResponse(BaseModel):
    jobs: list[JobCreateResponse]


class HistoryRecordResponse(BaseModel):
    job_id: str
    original_filename: str
    status: str
    processing_mode: str
    total_pages: int
    input_size_bytes: int
    output_size_bytes: int
    created_at: datetime
    completed_at: datetime | None
    download_url: str | None = None
    preview_url: str | None = None

