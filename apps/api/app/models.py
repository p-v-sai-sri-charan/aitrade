from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    exchange: Mapped[str] = mapped_column(String)
    symbol: Mapped[str] = mapped_column(String, index=True)
    company_name: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    filled_quantity: Mapped[int] = mapped_column(Integer, default=0)
    order_type: Mapped[str] = mapped_column(String)
    limit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average_fill_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product: Mapped[str] = mapped_column(String)
    validity: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    brokerage: Mapped[float] = mapped_column(Float, default=0.0)
    taxes: Mapped[float] = mapped_column(Float, default=0.0)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class PositionModel(Base):
    __tablename__ = "positions"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    company_name: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    average_price: Mapped[float] = mapped_column(Float)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)


class PortfolioStateModel(Base):
    __tablename__ = "portfolio_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    available_balance: Mapped[float] = mapped_column(Float)
    realized_pnl_today: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_reset_date: Mapped[str] = mapped_column(String, default="")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    original_transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parsed_intent: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ai_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    validation_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_errors: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    risk_check: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    user_confirmed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    order_response_summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class SettingsModel(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    ai_provider: Mapped[str] = mapped_column(String, default="mock")
    language_preference: Mapped[str] = mapped_column(String, default="auto")
    voice_output_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    risk_max_order_value: Mapped[float] = mapped_column(Float, default=200_000)
    risk_max_quantity: Mapped[int] = mapped_column(Integer, default=5_000)
    risk_max_price_deviation_pct: Mapped[float] = mapped_column(Float, default=5.0)
    risk_daily_loss_limit: Mapped[float] = mapped_column(Float, default=25_000)
    trading_kill_switch: Mapped[bool] = mapped_column(Boolean, default=False)


class IdempotencyKeyModel(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    response_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
