from __future__ import annotations

import hashlib
import socket
from pathlib import Path

import fitz
from fastapi import HTTPException

from app.core.config import get_settings


class SecureUploadValidator:
    """Validate PDFs beyond file extension checks."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def validate_pdf(self, path: Path) -> str:
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=400, detail="Uploaded file could not be saved correctly.")

        header = path.read_bytes()[:8]
        if not header.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

        self._run_malware_checks(path)
        try:
            with fitz.open(path) as document:
                if document.is_encrypted:
                    raise HTTPException(status_code=400, detail="Encrypted PDFs are not currently supported.")
                _ = document.page_count
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"The uploaded PDF could not be parsed: {exc}") from exc

        return self.sha256_for_file(path)

    def sha256_for_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _run_malware_checks(self, path: Path) -> None:
        if not self.settings.enable_malware_scan:
            return
        if self.settings.clamav_host:
            self._ping_clamav()

        suspicious_markers = (b"powershell.exe", b"cmd.exe", b"<script", b"javascript:")
        payload = path.read_bytes()[:1024 * 256].lower()
        if any(marker in payload for marker in suspicious_markers):
            raise HTTPException(status_code=400, detail="The uploaded PDF failed security validation.")

    def _ping_clamav(self) -> None:
        try:
            with socket.create_connection((self.settings.clamav_host, self.settings.clamav_port), timeout=3):
                return
        except OSError as exc:
            raise HTTPException(status_code=503, detail="Malware scanner is enabled but unavailable.") from exc
