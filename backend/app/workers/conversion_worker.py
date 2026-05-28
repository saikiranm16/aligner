from app.core.config import get_settings
from app.services.conversion_service import ConversionService
from app.services.job_manager import JobManager


settings = get_settings()
job_manager = JobManager(max_concurrent_jobs=settings.max_concurrent_jobs)
conversion_service = ConversionService(job_manager=job_manager)

