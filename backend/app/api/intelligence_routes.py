from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.models.database import get_db
from app.schemas.analysis import DashboardStatsResponse, ExportFormat, InsightResponse, SummaryRequest, SummaryResponse
from app.services.dashboard_service import DashboardService
from app.services.document_intelligence import DocumentIntelligenceService
from app.services.text_extractor import TextExtractorService
from app.workers.conversion_worker import conversion_service

router = APIRouter(tags=["intelligence"])
intelligence_service = DocumentIntelligenceService()
text_extractor = TextExtractorService()
dashboard_service = DashboardService()


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard(session: AsyncSession = Depends(get_db), current_user=Depends(get_optional_user)) -> DashboardStatsResponse:
    return await dashboard_service.get_stats(session, user_id=current_user.id if current_user else None)


@router.post("/jobs/{job_id}/summary", response_model=SummaryResponse)
async def summarize_document(
    job_id: str,
    payload: SummaryRequest,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
) -> SummaryResponse:
    record = await conversion_service.get_record(job_id, session)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if current_user and record.user_id is not None and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this document.")

    text = _extract_source_text(record, payload.source_type)
    try:
        return intelligence_service.summarize(
            job_id=job_id,
            source_type=payload.source_type,
            text=text,
            mode=payload.mode,
            length=payload.length,
            language_hint=payload.language_hint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/summary/export")
async def export_summary(
    job_id: str,
    source_type: str = Query(default="pdf"),
    mode: str = Query(default="extractive"),
    length: str = Query(default="medium"),
    format_type: ExportFormat = Query(default="txt"),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
) -> FileResponse:
    summary = await summarize_document(
        job_id,
        SummaryRequest(source_type=source_type, mode=mode, length=length),
        session,
        current_user,
    )
    export_path = intelligence_service.export_summary(
        job_id=job_id,
        summary=summary,
        output_dir=conversion_service.storage.settings.summaries_dir,
        format_type=format_type,
    )
    return FileResponse(export_path, filename=export_path.name)


@router.get("/jobs/{job_id}/insights", response_model=InsightResponse)
async def get_document_insights(
    job_id: str,
    source_type: str = Query(default="pdf"),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
) -> InsightResponse:
    record = await conversion_service.get_record(job_id, session)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if current_user and record.user_id is not None and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this document.")
    text = _extract_source_text(record, source_type)
    try:
        return intelligence_service.analyze(job_id=job_id, source_type=source_type, text=text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _extract_source_text(record, source_type: str) -> str:
    if source_type == "docx":
        if not record.output_docx_path:
            raise HTTPException(status_code=400, detail="DOCX output is not available for this job yet.")
        return text_extractor.extract_docx_text(Path(record.output_docx_path))
    return text_extractor.extract_pdf_text(Path(record.stored_pdf_path))
