from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.routers import (
    audit_logs,
    instruments,
    intent,
    orders,
    portfolio,
    positions,
    quotes,
    settings as settings_router,
    websocket,
)
from app.seed import seed_demo_data
from app.security import configure_cors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vaanitrade.api")

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    if settings.environment != "test":
        db = SessionLocal()
        try:
            seed_demo_data(db, settings)
        finally:
            db.close()
    logger.info("VaaniTrade API started. AI provider=%s environment=%s", settings.ai_provider, settings.environment)
    yield


app = FastAPI(
    title="VaaniTrade API",
    description=(
        "Backend for VaaniTrade, an open-source, voice-enabled Indian PAPER "
        "TRADING assistant. Paper trading only -- not connected to any real "
        "broker or exchange."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

configure_cors(app, settings)

API_PREFIX = "/api/v1"
app.include_router(intent.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(portfolio.router, prefix=API_PREFIX)
app.include_router(positions.router, prefix=API_PREFIX)
app.include_router(quotes.router, prefix=API_PREFIX)
app.include_router(instruments.router, prefix=API_PREFIX)
app.include_router(audit_logs.router, prefix=API_PREFIX)
app.include_router(settings_router.router, prefix=API_PREFIX)
app.include_router(websocket.router, prefix="/ws")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "paper-trading-only"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak internals (stack traces, secrets) to the client; log server-side instead.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})
