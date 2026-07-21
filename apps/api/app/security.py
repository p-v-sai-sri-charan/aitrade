"""Security helpers: CORS wiring, a rate-limit placeholder, and input
sanitization. No secrets are ever logged from here.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(text: str, max_length: int = 500) -> str:
    """Strip control characters and cap length before an AI call or DB write."""
    cleaned = _CONTROL_CHARS_RE.sub("", text).strip()
    return cleaned[:max_length]


def configure_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class InMemoryRateLimiter:
    """A simple sliding-window rate limiter.

    This is a PLACEHOLDER: it is per-process, in-memory, and resets on
    restart, which is fine for a single local/demo deployment. In
    production, back this with Redis (the project is "Redis-ready" --
    REDIS_URL is already configured) so limits are shared across workers.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
            )
        hits.append(now)


order_action_rate_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60)


def rate_limit_order_actions(request: Request) -> None:
    client_key = request.client.host if request.client else "unknown"
    order_action_rate_limiter.check(client_key)
