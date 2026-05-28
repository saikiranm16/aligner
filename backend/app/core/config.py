from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="AlignPDF", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    max_batch_size: int = Field(default=5, alias="MAX_BATCH_SIZE")
    job_retention_hours: int = Field(default=24, alias="JOB_RETENTION_HOURS")
    max_concurrent_jobs: int = Field(default=2, alias="MAX_CONCURRENT_JOBS")
    rate_limit_requests: int = Field(default=60, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    storage_root: Path = Field(default=Path("./data"), alias="STORAGE_ROOT")
    database_url: str = Field(default="sqlite+aiosqlite:///./data/app.db", alias="DATABASE_URL")
    ocr_languages: str = Field(default="eng", alias="OCR_LANGUAGES")
    ocr_dpi: int = Field(default=300, alias="OCR_DPI")
    enable_layout_refiner: bool = Field(default=True, alias="ENABLE_LAYOUT_REFINER")
    preview_render_zoom: float = Field(default=1.5, alias="PREVIEW_RENDER_ZOOM")
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173", alias="CORS_ORIGINS")
    tesseract_cmd: str = Field(default="", alias="TESSERACT_CMD")
    auth_secret_key: str = Field(default="change-me-alignpdf-secret", alias="AUTH_SECRET_KEY")
    auth_token_expiry_minutes: int = Field(default=60 * 12, alias="AUTH_TOKEN_EXPIRY_MINUTES")
    enable_malware_scan: bool = Field(default=False, alias="ENABLE_MALWARE_SCAN")
    clamav_host: str = Field(default="", alias="CLAMAV_HOST")
    clamav_port: int = Field(default=3310, alias="CLAMAV_PORT")
    summary_default_model: str = Field(default="facebook/bart-large-cnn", alias="SUMMARY_DEFAULT_MODEL")
    classification_default_model: str = Field(default="facebook/bart-large-mnli", alias="CLASSIFICATION_DEFAULT_MODEL")
    sentiment_default_model: str = Field(default="distilbert-base-uncased-finetuned-sst-2-english", alias="SENTIMENT_DEFAULT_MODEL")
    ai_cache_ttl_minutes: int = Field(default=120, alias="AI_CACHE_TTL_MINUTES")
    enable_transformers: bool = Field(default=True, alias="ENABLE_TRANSFORMERS")

    @property
    def uploads_dir(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.storage_root / "outputs"

    @property
    def previews_dir(self) -> Path:
        return self.storage_root / "previews"

    @property
    def preview_assets_dir(self) -> Path:
        return self.previews_dir / "assets"

    @property
    def summaries_dir(self) -> Path:
        return self.storage_root / "summaries"

    @property
    def cache_dir(self) -> Path:
        return self.storage_root / "cache"

    @property
    def temp_dir(self) -> Path:
        return self.storage_root / "temp"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
