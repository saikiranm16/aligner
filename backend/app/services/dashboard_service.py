from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.history import ConversionHistory
from app.schemas.analysis import DashboardStatsResponse


class DashboardService:
    """Aggregate lightweight dashboard statistics from conversion history."""

    async def get_stats(self, session: AsyncSession, user_id: int | None = None) -> DashboardStatsResponse:
        query = select(ConversionHistory).order_by(ConversionHistory.created_at.desc())
        if user_id is not None:
            query = query.where(ConversionHistory.user_id == user_id)
        result = await session.execute(query)
        records = result.scalars().all()

        total_jobs = len(records)
        completed_jobs = sum(record.status == "completed" for record in records)
        failed_jobs = sum(record.status == "failed" for record in records)
        queued_jobs = total_jobs - completed_jobs - failed_jobs
        total_pages = sum(record.total_pages for record in records)
        avg_output_size = (
            sum(record.output_size_bytes for record in records) / completed_jobs if completed_jobs else 0.0
        )

        return DashboardStatsResponse(
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            queued_jobs=queued_jobs,
            total_pages_processed=total_pages,
            average_output_size_bytes=avg_output_size,
            latest_job_filename=records[0].original_filename if records else None,
        )
