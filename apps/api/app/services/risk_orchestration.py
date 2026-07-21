"""Shared order evaluation logic used by both /orders/preview and
/orders/confirm, so confirmation re-checks risk against the *current* state
rather than trusting the numbers shown in an earlier preview.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from broker_core import compute_charges, resolve_instrument
from broker_core.market_data import get_quote
from broker_core.models import OrderRequest
from broker_core.paper_broker import PaperBroker
from broker_core.pricing import PaperBrokerConfig
from risk_engine import (
    OrderRequestContext,
    RecentOrderFingerprint,
    RiskCheckResult,
    RiskContext,
    RiskLimits,
    run_risk_checks,
)

from app.schemas import OrderRequestSchema


@dataclass
class OrderEvaluation:
    order_request: OrderRequest
    company_name: str
    risk_check: RiskCheckResult
    estimated_price: float
    estimated_value: float
    estimated_brokerage: float
    estimated_taxes: float
    estimated_total: float


async def evaluate_order(
    input: OrderRequestSchema,
    *,
    broker: PaperBroker,
    limits: RiskLimits,
    trading_kill_switch_active: bool,
    paper_config: PaperBrokerConfig,
) -> OrderEvaluation:
    resolved = resolve_instrument(input.symbol)
    quote = get_quote(resolved.instrument.symbol) if resolved.instrument else None
    market_price = quote.last_price if quote else None

    balance = broker.store.get_balance()
    portfolio = await broker.get_portfolio()

    since = datetime.now(timezone.utc) - timedelta(seconds=limits.duplicate_order_window_seconds)
    recent = broker.store.list_recent_orders(since)
    recent_fingerprints = [
        RecentOrderFingerprint(
            symbol=o.symbol,
            side=o.side,
            quantity=o.quantity,
            order_type=o.order_type,
            limit_price=o.limit_price,
            placed_at=o.created_at,
        )
        for o in recent
        if o.status in ("FILLED", "PENDING")
    ]

    order_ctx = OrderRequestContext(
        exchange=input.exchange,
        symbol=input.symbol,
        side=input.side,
        quantity=input.quantity,
        order_type=input.order_type,
        limit_price=input.limit_price,
        product=input.product,
        validity=input.validity,
        missing_fields=[],
        ambiguous_symbol_candidates=[c.symbol for c in resolved.candidates],
        symbol_resolved=resolved.instrument is not None,
    )

    risk_ctx = RiskContext(
        order=order_ctx,
        limits=limits,
        available_balance=balance,
        market_price=market_price,
        day_realized_and_unrealized_pnl=portfolio.day_pnl,
        recent_orders=recent_fingerprints,
        now=datetime.now(timezone.utc),
        trading_kill_switch_active=trading_kill_switch_active,
        market_open=True,
    )

    risk_check = run_risk_checks(risk_ctx)

    reference_price = input.limit_price if input.order_type == "LIMIT" else market_price
    reference_price = reference_price or 0.0
    value = round(reference_price * input.quantity, 2)
    brokerage, taxes = compute_charges(input.side, value, paper_config)
    total = round(value + brokerage + taxes, 2) if input.side == "BUY" else round(value - brokerage - taxes, 2)

    company_name = resolved.instrument.company_name if resolved.instrument else input.symbol

    order_request = OrderRequest(
        exchange=input.exchange,
        symbol=resolved.instrument.symbol if resolved.instrument else input.symbol,
        company_name=company_name,
        side=input.side,
        quantity=input.quantity,
        order_type=input.order_type,
        limit_price=input.limit_price,
        product=input.product,
        validity=input.validity,
    )

    return OrderEvaluation(
        order_request=order_request,
        company_name=company_name,
        risk_check=risk_check,
        estimated_price=round(reference_price, 2),
        estimated_value=value,
        estimated_brokerage=brokerage,
        estimated_taxes=taxes,
        estimated_total=total,
    )
