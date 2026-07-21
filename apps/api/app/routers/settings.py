from __future__ import annotations

from fastapi import APIRouter

from app.audit import write_audit_log
from app.deps import AppSettings, DbSession
from app.models import OrderModel, PositionModel
from app.repositories import get_or_create_portfolio_state, get_or_create_settings
from app.schemas import RiskLimitsSchema, SettingsSchema, SettingsUpdateSchema

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_schema(row) -> SettingsSchema:  # noqa: ANN001
    return SettingsSchema(
        aiProvider=row.ai_provider,
        languagePreference=row.language_preference,
        voiceOutputEnabled=row.voice_output_enabled,
        riskLimits=RiskLimitsSchema(
            maxOrderValue=row.risk_max_order_value,
            maxQuantity=row.risk_max_quantity,
            maxPriceDeviationPct=row.risk_max_price_deviation_pct,
            dailyLossLimit=row.risk_daily_loss_limit,
        ),
        tradingKillSwitch=row.trading_kill_switch,
    )


@router.get("", response_model=SettingsSchema)
async def get_settings_endpoint(db: DbSession, settings: AppSettings) -> SettingsSchema:
    row = get_or_create_settings(db, settings)
    return _to_schema(row)


@router.put("", response_model=SettingsSchema)
async def update_settings_endpoint(
    payload: SettingsUpdateSchema, db: DbSession, settings: AppSettings
) -> SettingsSchema:
    row = get_or_create_settings(db, settings)

    if payload.ai_provider is not None:
        row.ai_provider = payload.ai_provider
    if payload.language_preference is not None:
        row.language_preference = payload.language_preference
    if payload.voice_output_enabled is not None:
        row.voice_output_enabled = payload.voice_output_enabled
    if payload.trading_kill_switch is not None:
        row.trading_kill_switch = payload.trading_kill_switch
    if payload.risk_limits is not None:
        row.risk_max_order_value = payload.risk_limits.max_order_value
        row.risk_max_quantity = payload.risk_limits.max_quantity
        row.risk_max_price_deviation_pct = payload.risk_limits.max_price_deviation_pct
        row.risk_daily_loss_limit = payload.risk_limits.daily_loss_limit

    db.commit()
    db.refresh(row)
    return _to_schema(row)


@router.post("/reset-paper-trading", response_model=SettingsSchema)
async def reset_paper_trading(db: DbSession, settings: AppSettings) -> SettingsSchema:
    """Wipes all paper orders/positions and restores the starting balance.
    Never touches real money -- this project supports paper trading only.
    """
    db.query(OrderModel).delete()
    db.query(PositionModel).delete()

    state = get_or_create_portfolio_state(db, settings)
    state.available_balance = settings.paper_starting_balance
    state.realized_pnl_today = 0.0
    db.commit()

    write_audit_log(
        db,
        order_response_summary="Paper trading account reset by user.",
        validation_valid=True,
    )

    row = get_or_create_settings(db, settings)
    return _to_schema(row)
