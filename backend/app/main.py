from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.auth_routes import router as auth_router
from app.api.intelligence_routes import router as intelligence_router
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.migrations import run_startup_migrations
from app.core.rate_limit import rate_limiter
from app.models.database import Base, engine
from app.models import history as _history  # noqa: F401
from app.models import user as _user  # noqa: F401
from app.workers.conversion_worker import conversion_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize logging, database tables, and storage directories."""

    configure_logging()
    conversion_service.storage  # Touch the storage service so directories exist on boot.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await run_startup_migrations(engine)
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def apply_rate_limit(request: Request, call_next):
    await rate_limiter.check(request)
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if request.app.debug:
        raise exc
    return JSONResponse(status_code=500, content={"detail": "AlignPDF encountered an unexpected error."})


app.include_router(router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(intelligence_router, prefix=settings.api_prefix)


@app.get("/health")
async def root_healthcheck() -> dict[str, str]:
    return {"status": "ok"}
