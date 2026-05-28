from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.core.config import get_settings
from app.models.database import get_db
from app.schemas.jobs import BatchJobCreateResponse, HistoryRecordResponse, JobCreateResponse, JobProgressResponse, JobState
from app.services.file_validation import SecureUploadValidator
from app.services.storage import StorageService
from app.workers.conversion_worker import conversion_service, job_manager

router = APIRouter()
settings = get_settings()
storage = StorageService()
validator = SecureUploadValidator()


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/jobs", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
) -> JobCreateResponse:
    _validate_upload(file)
    pdf_path: Path | None = None
    try:
        job_id, pdf_path, input_size = await storage.save_upload(file)
        validator.validate_pdf(pdf_path)
    except HTTPException as exc:
        if pdf_path is not None:
            pdf_path.unlink(missing_ok=True)
        raise exc
    except ValueError as exc:
        if pdf_path is not None:
            pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await conversion_service.queue_job(
        job_id=job_id,
        filename=file.filename or "document.pdf",
        pdf_path=pdf_path,
        input_size=input_size,
        session=session,
        user_id=current_user.id if current_user else None,
    )
    await conversion_service.start_job(job_id, file.filename or "document.pdf", pdf_path)
    return JobCreateResponse(job_id=job_id, filename=file.filename or "document.pdf", status=JobState.QUEUED)


@router.post("/jobs/batch", response_model=BatchJobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_batch_jobs(
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
) -> BatchJobCreateResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF is required.")
    if len(files) > settings.max_batch_size:
        raise HTTPException(status_code=400, detail=f"Batch limit is {settings.max_batch_size} files.")

    jobs = []
    for file in files:
        _validate_upload(file)
        pdf_path: Path | None = None
        try:
            job_id, pdf_path, input_size = await storage.save_upload(file)
            validator.validate_pdf(pdf_path)
        except HTTPException as exc:
            if pdf_path is not None:
                pdf_path.unlink(missing_ok=True)
            raise exc
        except ValueError as exc:
            if pdf_path is not None:
                pdf_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        filename = file.filename or "document.pdf"
        await conversion_service.queue_job(
            job_id=job_id,
            filename=filename,
            pdf_path=pdf_path,
            input_size=input_size,
            session=session,
            user_id=current_user.id if current_user else None,
        )
        await conversion_service.start_job(job_id, filename, pdf_path)
        jobs.append(JobCreateResponse(job_id=job_id, filename=filename, status=JobState.QUEUED))

    return BatchJobCreateResponse(jobs=jobs)


@router.get("/jobs/{job_id}", response_model=JobProgressResponse)
async def get_job(job_id: str) -> JobProgressResponse:
    response = await job_manager.get_response(job_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return response


@router.post("/jobs/{job_id}/retry", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_job(job_id: str, session: AsyncSession = Depends(get_db), current_user=Depends(get_optional_user)) -> JobCreateResponse:
    record = await conversion_service.get_record(job_id, session)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if current_user and record.user_id is not None and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this document.")
    if not Path(record.stored_pdf_path).exists():
        raise HTTPException(status_code=404, detail="Original PDF is no longer available for retry.")

    new_job_id = uuid4().hex
    await conversion_service.queue_job(
        job_id=new_job_id,
        filename=record.original_filename,
        pdf_path=Path(record.stored_pdf_path),
        input_size=record.input_size_bytes,
        session=session,
        user_id=record.user_id,
    )
    await conversion_service.start_job(new_job_id, record.original_filename, Path(record.stored_pdf_path))
    return JobCreateResponse(job_id=new_job_id, filename=record.original_filename, status=JobState.QUEUED)


@router.get("/jobs/{job_id}/download")
async def download_docx(job_id: str, session: AsyncSession = Depends(get_db), current_user=Depends(get_optional_user)) -> FileResponse:
    record = await conversion_service.get_record(job_id, session)
    if record is None or not record.output_docx_path:
        raise HTTPException(status_code=404, detail="Converted DOCX not found.")
    if current_user and record.user_id is not None and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this document.")
    path = Path(record.output_docx_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Converted DOCX file is missing.")
    output_name = f"{Path(record.original_filename).stem}.docx"
    return FileResponse(path=path, filename=output_name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.get("/jobs/{job_id}/preview")
async def get_preview(job_id: str, session: AsyncSession = Depends(get_db), current_user=Depends(get_optional_user)) -> HTMLResponse:
    record = await conversion_service.get_record(job_id, session)
    if record is None or not record.preview_html_path:
        raise HTTPException(status_code=404, detail="Preview not found.")
    if current_user and record.user_id is not None and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this document.")
    preview_path = Path(record.preview_html_path)
    if not preview_path.exists():
        raise HTTPException(status_code=404, detail="Preview file is missing.")
    return HTMLResponse(preview_path.read_text(encoding="utf-8"))


@router.get("/jobs/{job_id}/preview-assets/{asset_name}")
async def get_preview_asset(
    job_id: str,
    asset_name: str,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
) -> FileResponse:
    record = await conversion_service.get_record(job_id, session)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if current_user and record.user_id is not None and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this document.")
    asset_path = storage.build_preview_asset_dir(job_id) / asset_name
    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="Preview asset not found.")
    return FileResponse(asset_path)


@router.get("/history", response_model=list[HistoryRecordResponse])
async def list_history(session: AsyncSession = Depends(get_db), current_user=Depends(get_optional_user)) -> list[HistoryRecordResponse]:
    return await conversion_service.get_history(session, user_id=current_user.id if current_user else None)


def _validate_upload(file: UploadFile) -> None:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
