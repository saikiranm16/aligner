from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


class StorageService:
    """Handle local file storage paths for uploads, outputs, previews, and temp assets."""

    def __init__(self) -> None:
        self.settings = get_settings()
        for directory in (
            self.settings.storage_root,
            self.settings.uploads_dir,
            self.settings.outputs_dir,
            self.settings.previews_dir,
            self.settings.preview_assets_dir,
            self.settings.summaries_dir,
            self.settings.cache_dir,
            self.settings.temp_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> tuple[str, Path, int]:
        """Persist the uploaded PDF and return its job id, path, and size."""

        job_id = uuid4().hex
        safe_name = Path(upload.filename or "document.pdf").name
        target_path = self.settings.uploads_dir / f"{job_id}_{safe_name}"

        size = 0
        with target_path.open("wb") as buffer:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > self.settings.max_file_size_mb * 1024 * 1024:
                    buffer.close()
                    target_path.unlink(missing_ok=True)
                    await upload.close()
                    raise ValueError(f"File exceeds the {self.settings.max_file_size_mb} MB limit.")
                buffer.write(chunk)

        await upload.close()
        return job_id, target_path, size

    def build_output_path(self, job_id: str, original_name: str) -> Path:
        stem = Path(original_name).stem
        return self.settings.outputs_dir / f"{job_id}_{stem}.docx"

    def build_preview_path(self, job_id: str) -> Path:
        return self.settings.previews_dir / f"{job_id}.html"

    def build_preview_asset_dir(self, job_id: str) -> Path:
        asset_dir = self.settings.preview_assets_dir / job_id
        asset_dir.mkdir(parents=True, exist_ok=True)
        return asset_dir

    def create_temp_dir(self, job_id: str) -> Path:
        temp_dir = self.settings.temp_dir / job_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def cleanup_temp_dir(self, job_id: str) -> None:
        temp_dir = self.settings.temp_dir / job_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
