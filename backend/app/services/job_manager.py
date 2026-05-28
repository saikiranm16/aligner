from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.jobs import JobProgressResponse, JobState

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    """In-memory status object used for live progress polling."""

    job_id: str
    filename: str
    status: JobState = JobState.QUEUED
    progress: int = 0
    stage_message: str = "Queued for conversion"
    mode: str | None = None
    error_message: str | None = None
    download_url: str | None = None
    preview_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class JobManager:
    """Track live jobs and provide a concurrency gate for CPU-heavy work."""

    def __init__(self, max_concurrent_jobs: int) -> None:
        self.jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)

    async def register(self, job_id: str, filename: str) -> JobRecord:
        async with self._lock:
            record = JobRecord(job_id=job_id, filename=filename)
            self.jobs[job_id] = record
            return record

    async def update(
        self,
        job_id: str,
        *,
        status: JobState | None = None,
        progress: int | None = None,
        stage_message: str | None = None,
        mode: str | None = None,
        error_message: str | None = None,
        download_url: str | None = None,
        preview_url: str | None = None,
        completed: bool = False,
    ) -> None:
        async with self._lock:
            record = self.jobs[job_id]
            if status is not None:
                record.status = status
            if progress is not None:
                record.progress = progress
            if stage_message is not None:
                record.stage_message = stage_message
            if mode is not None:
                record.mode = mode
            if error_message is not None:
                record.error_message = error_message
            if download_url is not None:
                record.download_url = download_url
            if preview_url is not None:
                record.preview_url = preview_url
            if completed:
                record.completed_at = datetime.utcnow()

    async def get(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self.jobs.get(job_id)

    async def get_response(self, job_id: str) -> JobProgressResponse | None:
        record = await self.get(job_id)
        if record is None:
            return None
        return JobProgressResponse(
            job_id=record.job_id,
            filename=record.filename,
            status=record.status,
            progress=record.progress,
            stage_message=record.stage_message,
            mode=record.mode,
            error_message=record.error_message,
            download_url=record.download_url,
            preview_url=record.preview_url,
            created_at=record.created_at,
            completed_at=record.completed_at,
        )

    async def run(self, task_factory) -> None:
        """Run a coroutine under the job concurrency limiter."""

        async with self._semaphore:
            await task_factory()

