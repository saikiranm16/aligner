from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.history import ConversionHistory
from app.schemas.jobs import HistoryRecordResponse, JobState
from app.services.docx_builder import DocxBuilder
from app.services.job_manager import JobManager
from app.services.layout_analyzer import LayoutAnalyzer
from app.services.layout_refiner import LayoutRefiner
from app.services.ocr_service import OcrService
from app.services.pdf_detector import PdfDetector
from app.services.preview_renderer import PreviewRenderer
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class ConversionService:
    """Orchestrate detection, extraction, OCR fallback, preview generation, and DOCX export."""

    def __init__(self, job_manager: JobManager) -> None:
        self.settings = get_settings()
        self.job_manager = job_manager
        self.storage = StorageService()
        self.detector = PdfDetector()
        self.ocr_service = OcrService()
        self.analyzer = LayoutAnalyzer(self.ocr_service)
        self.refiner = LayoutRefiner()
        self.preview_renderer = PreviewRenderer()
        self.docx_builder = DocxBuilder()

    async def queue_job(
        self,
        *,
        job_id: str,
        filename: str,
        pdf_path: Path,
        input_size: int,
        session: AsyncSession,
        user_id: int | None = None,
    ) -> None:
        await self.job_manager.register(job_id, filename)
        session.add(
            ConversionHistory(
                job_id=job_id,
                user_id=user_id,
                original_filename=filename,
                stored_pdf_path=str(pdf_path),
                status=JobState.QUEUED.value,
                input_size_bytes=input_size,
            )
        )
        await session.commit()

    async def start_job(self, job_id: str, filename: str, pdf_path: Path) -> None:
        asyncio.create_task(
            self.job_manager.run(lambda: self._run_job(job_id=job_id, filename=filename, pdf_path=pdf_path))
        )

    async def _run_job(self, *, job_id: str, filename: str, pdf_path: Path) -> None:
        temp_dir = self.storage.create_temp_dir(job_id)
        try:
            await self.job_manager.update(job_id, status=JobState.ANALYZING, progress=10, stage_message="Analyzing PDF structure")
            detection = await asyncio.to_thread(self.detector.inspect_pdf, pdf_path)
            mode = detection["mode"]
            await self.job_manager.update(job_id, mode=mode)

            if mode in {"scanned", "mixed"}:
                await self.job_manager.update(job_id, status=JobState.OCR, progress=30, stage_message="Running OCR on scanned pages")
            else:
                await self.job_manager.update(job_id, status=JobState.EXTRACTING, progress=30, stage_message="Extracting page layout")

            analysis = await asyncio.to_thread(
                self.analyzer.extract_layout,
                pdf_path,
                detection,
                temp_dir,
                filename,
                self.settings.ocr_languages,
            )

            if self.settings.enable_layout_refiner:
                analysis = await asyncio.to_thread(self.refiner.refine, analysis)

            output_path = self.storage.build_output_path(job_id, filename)
            await self.job_manager.update(job_id, status=JobState.BUILDING, progress=70, stage_message="Building editable DOCX")
            await asyncio.to_thread(self.docx_builder.build, analysis, output_path)

            preview_path = self.storage.build_preview_path(job_id)
            preview_asset_dir = self.storage.build_preview_asset_dir(job_id)
            await self.job_manager.update(job_id, status=JobState.PREVIEWING, progress=85, stage_message="Rendering preview")
            await asyncio.to_thread(self.preview_renderer.render, pdf_path, preview_path, preview_asset_dir, job_id, filename)

            await self._persist_result(
                job_id=job_id,
                status=JobState.COMPLETED,
                mode=mode,
                page_count=analysis.page_count,
                output_path=output_path,
                preview_path=preview_path,
            )
            await self.job_manager.update(
                job_id,
                status=JobState.COMPLETED,
                progress=100,
                stage_message="Conversion completed",
                download_url=f"{self.settings.api_prefix}/jobs/{job_id}/download",
                preview_url=f"{self.settings.api_prefix}/jobs/{job_id}/preview",
                completed=True,
            )
        except Exception as exc:  # pragma: no cover - end-to-end error path
            logger.exception("Conversion failed for job %s", job_id)
            await self._persist_result(job_id=job_id, status=JobState.FAILED, error_message=str(exc))
            await self.job_manager.update(
                job_id,
                status=JobState.FAILED,
                progress=100,
                stage_message="Conversion failed",
                error_message=str(exc),
                completed=True,
            )
        finally:
            self.storage.cleanup_temp_dir(job_id)

    async def _persist_result(
        self,
        *,
        job_id: str,
        status: JobState,
        mode: str | None = None,
        page_count: int = 0,
        output_path: Path | None = None,
        preview_path: Path | None = None,
        error_message: str = "",
    ) -> None:
        from app.models.database import SessionLocal

        async with SessionLocal() as session:
            result = await session.execute(select(ConversionHistory).where(ConversionHistory.job_id == job_id))
            record = result.scalar_one()
            record.status = status.value
            record.processing_mode = mode or record.processing_mode
            record.total_pages = page_count or record.total_pages
            record.output_docx_path = str(output_path) if output_path else record.output_docx_path
            record.preview_html_path = str(preview_path) if preview_path else record.preview_html_path
            record.output_size_bytes = output_path.stat().st_size if output_path and output_path.exists() else 0
            record.error_message = error_message
            record.completed_at = datetime.utcnow()
            await session.commit()

    async def get_history(self, session: AsyncSession, user_id: int | None = None) -> list[HistoryRecordResponse]:
        query = select(ConversionHistory).order_by(ConversionHistory.created_at.desc())
        if user_id is not None:
            query = query.where(ConversionHistory.user_id == user_id)
        result = await session.execute(query)
        records = result.scalars().all()
        return [
            HistoryRecordResponse(
                job_id=record.job_id,
                original_filename=record.original_filename,
                status=record.status,
                processing_mode=record.processing_mode,
                total_pages=record.total_pages,
                input_size_bytes=record.input_size_bytes,
                output_size_bytes=record.output_size_bytes,
                created_at=record.created_at,
                completed_at=record.completed_at,
                download_url=f"{self.settings.api_prefix}/jobs/{record.job_id}/download" if record.output_docx_path else None,
                preview_url=f"{self.settings.api_prefix}/jobs/{record.job_id}/preview" if record.preview_html_path else None,
            )
            for record in records
        ]

    async def get_record(self, job_id: str, session: AsyncSession) -> ConversionHistory | None:
        result = await session.execute(select(ConversionHistory).where(ConversionHistory.job_id == job_id))
        return result.scalar_one_or_none()
