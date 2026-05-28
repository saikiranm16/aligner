from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import get_settings


class CacheService:
    """Small file-based cache for AI summaries and document insights."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, namespace: str, key: str) -> dict | None:
        path = self._path_for(namespace, key)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        expires_at = datetime.fromisoformat(payload["expires_at"])
        if expires_at < datetime.now(UTC):
            path.unlink(missing_ok=True)
            return None
        return payload["value"]

    def set(self, namespace: str, key: str, value: dict) -> None:
        path = self._path_for(namespace, key)
        expires_at = datetime.now(UTC) + timedelta(minutes=self.settings.ai_cache_ttl_minutes)
        path.write_text(
            json.dumps({"expires_at": expires_at.isoformat(), "value": value}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def build_key(*parts: str) -> str:
        joined = "::".join(parts)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def _path_for(self, namespace: str, key: str) -> Path:
        namespace_dir = self.settings.cache_dir / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)
        return namespace_dir / f"{key}.json"
