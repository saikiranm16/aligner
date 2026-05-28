from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


class InMemoryRateLimiter:
    """Simple per-IP sliding-window limiter suitable for a single-node deployment."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, request: Request) -> None:
        identifier = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - self.settings.rate_limit_window_seconds

        async with self._lock:
            bucket = self._hits[identifier]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self.settings.rate_limit_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please slow down and try again.",
                )
            bucket.append(now)


rate_limiter = InMemoryRateLimiter()

