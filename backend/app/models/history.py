from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class ConversionHistory(Base):
    """Persisted metadata for completed and failed conversions."""

    __tablename__ = "conversion_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_pdf_path: Mapped[str] = mapped_column(String(512))
    output_docx_path: Mapped[str] = mapped_column(String(512), default="")
    preview_html_path: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(32), index=True)
    processing_mode: Mapped[str] = mapped_column(String(32), default="unknown")
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    input_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    output_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
