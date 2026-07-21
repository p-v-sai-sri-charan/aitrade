from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ai_providers import AIProvider, create_provider
from app.config import Settings, get_settings
from app.db import get_db
from app.repositories import SQLAlchemyBrokerStore, get_or_create_settings
from broker_core import PaperBroker, PaperBrokerConfig
from risk_engine import RiskLimits

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_ai_provider(db: DbSession, settings: AppSettings) -> AIProvider:
    """The active AI provider is chosen by AI_PROVIDER by default; the
    Settings screen may override it at runtime for convenience, but API
    keys always come from environment variables only.
    """
    settings_row = get_or_create_settings(db, settings)
    env = settings.ai_provider_env()
    env["AI_PROVIDER"] = settings_row.ai_provider
    return create_provider(env=env)


def get_broker(db: DbSession, settings: AppSettings) -> PaperBroker:
    store = SQLAlchemyBrokerStore(db, settings)
    config = PaperBrokerConfig(
        slippage_bps=settings.paper_slippage_bps,
        brokerage_flat=settings.paper_brokerage_flat,
        stt_rate_sell=settings.paper_stt_rate_sell,
        gst_rate=settings.paper_gst_rate,
    )
    return PaperBroker(store, config)


def get_risk_limits(db: DbSession, settings: AppSettings) -> RiskLimits:
    row = get_or_create_settings(db, settings)
    return RiskLimits(
        max_order_value=row.risk_max_order_value,
        max_quantity=row.risk_max_quantity,
        max_price_deviation_pct=row.risk_max_price_deviation_pct,
        daily_loss_limit=row.risk_daily_loss_limit,
        duplicate_order_window_seconds=settings.risk_duplicate_order_window_seconds,
    )


AIProviderDep = Annotated[AIProvider, Depends(get_ai_provider)]
BrokerDep = Annotated[PaperBroker, Depends(get_broker)]
RiskLimitsDep = Annotated[RiskLimits, Depends(get_risk_limits)]
