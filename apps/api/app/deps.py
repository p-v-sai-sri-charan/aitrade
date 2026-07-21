from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ai_providers import AIProvider, create_provider
from app.config import Settings, get_settings
from app.db import get_db
from app.repositories import SQLAlchemyBrokerStore, get_or_create_settings
from broker_core import (
    InstrumentRepository,
    MarketDataProvider,
    PaperBroker,
    PaperBrokerConfig,
    create_instrument_repository,
    create_market_data_provider,
)
from risk_engine import RiskLimits

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]

# These two hold in-memory caches (live quotes, the fetched NSE instrument
# universe) that only help if they persist across requests, so they're
# built once from the process-wide settings rather than per-request.
_settings = get_settings()
_market_data_provider: MarketDataProvider = create_market_data_provider(
    _settings.market_data_provider, cache_ttl_seconds=_settings.market_data_cache_ttl_seconds
)
_instrument_repository: InstrumentRepository = create_instrument_repository(
    _settings.instrument_source, cache_ttl_seconds=_settings.instrument_cache_ttl_seconds
)


def get_market_data_provider() -> MarketDataProvider:
    return _market_data_provider


def get_instrument_repository() -> InstrumentRepository:
    return _instrument_repository


def get_ai_provider(db: DbSession, settings: AppSettings) -> AIProvider:
    """The active AI provider is chosen by AI_PROVIDER by default; the
    Settings screen may override it at runtime for convenience, but API
    keys always come from environment variables only.
    """
    settings_row = get_or_create_settings(db, settings)
    env = settings.ai_provider_env()
    env["AI_PROVIDER"] = settings_row.ai_provider
    return create_provider(env=env)


def get_broker(
    db: DbSession,
    settings: AppSettings,
    market_data: Annotated[MarketDataProvider, Depends(get_market_data_provider)],
    instruments: Annotated[InstrumentRepository, Depends(get_instrument_repository)],
) -> PaperBroker:
    store = SQLAlchemyBrokerStore(db, settings)
    config = PaperBrokerConfig(
        slippage_bps=settings.paper_slippage_bps,
        brokerage_flat=settings.paper_brokerage_flat,
        stt_rate_sell=settings.paper_stt_rate_sell,
        gst_rate=settings.paper_gst_rate,
    )
    return PaperBroker(store, config, market_data=market_data, instruments=instruments)


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
InstrumentRepositoryDep = Annotated[InstrumentRepository, Depends(get_instrument_repository)]
