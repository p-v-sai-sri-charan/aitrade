from datetime import datetime, timedelta, timezone

import pytest

from risk_engine import (
    OrderRequestContext,
    RecentOrderFingerprint,
    RiskContext,
    RiskLimits,
    run_risk_checks,
)

NOW = datetime(2026, 7, 21, 10, 0, 0, tzinfo=timezone.utc)


def make_order(**overrides) -> OrderRequestContext:
    defaults = dict(
        exchange="NSE",
        symbol="RELIANCE",
        side="BUY",
        quantity=10,
        order_type="LIMIT",
        limit_price=2950.0,
        product="DELIVERY",
        validity="DAY",
        missing_fields=[],
        ambiguous_symbol_candidates=[],
        symbol_resolved=True,
    )
    defaults.update(overrides)
    return OrderRequestContext(**defaults)


def make_ctx(order: OrderRequestContext, **overrides) -> RiskContext:
    defaults = dict(
        order=order,
        limits=RiskLimits(),
        available_balance=1_000_000,
        market_price=2960.0,
        day_realized_and_unrealized_pnl=0.0,
        recent_orders=[],
        now=NOW,
        trading_kill_switch_active=False,
        market_open=True,
    )
    defaults.update(overrides)
    return RiskContext(**defaults)


def test_valid_order_allowed():
    ctx = make_ctx(make_order())
    result = run_risk_checks(ctx)
    assert result.allowed is True
    assert result.code == "OK"


def test_kill_switch_blocks_everything():
    ctx = make_ctx(make_order(), trading_kill_switch_active=True)
    result = run_risk_checks(ctx)
    assert result.allowed is False
    assert result.code == "TRADING_KILL_SWITCH_ACTIVE"


def test_daily_loss_limit():
    ctx = make_ctx(
        make_order(),
        day_realized_and_unrealized_pnl=-30_000,
        limits=RiskLimits(daily_loss_limit=25_000),
    )
    result = run_risk_checks(ctx)
    assert result.code == "DAILY_LOSS_LIMIT_EXCEEDED"


def test_missing_fields():
    ctx = make_ctx(make_order(missing_fields=["quantity"]))
    result = run_risk_checks(ctx)
    assert result.code == "MISSING_FIELDS"


def test_ambiguous_symbol():
    ctx = make_ctx(
        make_order(symbol=None, ambiguous_symbol_candidates=["TATASTEEL", "TATAMOTORS"])
    )
    result = run_risk_checks(ctx)
    assert result.code == "AMBIGUOUS_SYMBOL"


def test_symbol_not_found():
    ctx = make_ctx(make_order(symbol_resolved=False))
    result = run_risk_checks(ctx)
    assert result.code == "SYMBOL_NOT_FOUND"


def test_unsupported_exchange():
    ctx = make_ctx(make_order(exchange="BSE"))
    result = run_risk_checks(ctx)
    assert result.code == "UNSUPPORTED_EXCHANGE"


def test_unsupported_product():
    ctx = make_ctx(make_order(product="INTRADAY"))
    result = run_risk_checks(ctx)
    assert result.code == "UNSUPPORTED_PRODUCT"


def test_invalid_price_for_limit_order():
    ctx = make_ctx(make_order(limit_price=0))
    result = run_risk_checks(ctx)
    assert result.code == "INVALID_PRICE"


def test_max_quantity_exceeded():
    ctx = make_ctx(make_order(quantity=10_000), limits=RiskLimits(max_quantity=5_000))
    result = run_risk_checks(ctx)
    assert result.code == "MAX_QUANTITY_EXCEEDED"


def test_zero_quantity_rejected():
    ctx = make_ctx(make_order(quantity=0))
    result = run_risk_checks(ctx)
    assert result.code == "MAX_QUANTITY_EXCEEDED"


def test_order_value_limit_exceeded():
    ctx = make_ctx(
        make_order(quantity=1000, limit_price=2950),
        limits=RiskLimits(max_order_value=200_000),
    )
    result = run_risk_checks(ctx)
    assert result.code == "ORDER_VALUE_LIMIT_EXCEEDED"


def test_insufficient_balance():
    ctx = make_ctx(make_order(quantity=10, limit_price=2950), available_balance=1000)
    result = run_risk_checks(ctx)
    assert result.code == "INSUFFICIENT_BALANCE"


def test_insufficient_balance_not_checked_for_sell():
    ctx = make_ctx(
        make_order(side="SELL", quantity=10, limit_price=2950), available_balance=1000
    )
    result = run_risk_checks(ctx)
    assert result.allowed is True


def test_price_deviation_too_high():
    ctx = make_ctx(
        make_order(limit_price=5000),
        market_price=2950,
        limits=RiskLimits(max_price_deviation_pct=5),
    )
    result = run_risk_checks(ctx)
    assert result.code == "PRICE_DEVIATION_TOO_HIGH"
    assert result.requires_override is True


def test_duplicate_order_detected():
    recent = RecentOrderFingerprint(
        symbol="RELIANCE",
        side="BUY",
        quantity=10,
        order_type="LIMIT",
        limit_price=2950.0,
        placed_at=NOW - timedelta(seconds=3),
    )
    ctx = make_ctx(make_order(), recent_orders=[recent])
    result = run_risk_checks(ctx)
    assert result.code == "DUPLICATE_ORDER"
    assert result.requires_override is True


def test_duplicate_order_outside_window_allowed():
    recent = RecentOrderFingerprint(
        symbol="RELIANCE",
        side="BUY",
        quantity=10,
        order_type="LIMIT",
        limit_price=2950.0,
        placed_at=NOW - timedelta(seconds=60),
    )
    ctx = make_ctx(make_order(), recent_orders=[recent])
    result = run_risk_checks(ctx)
    assert result.allowed is True


def test_market_closed():
    ctx = make_ctx(make_order(), market_open=False)
    result = run_risk_checks(ctx)
    assert result.code == "MARKET_CLOSED"
    assert result.requires_override is True


@pytest.mark.parametrize("order_type", ["MARKET"])
def test_market_order_skips_price_deviation_check(order_type):
    ctx = make_ctx(make_order(order_type=order_type, limit_price=None))
    result = run_risk_checks(ctx)
    assert result.allowed is True
