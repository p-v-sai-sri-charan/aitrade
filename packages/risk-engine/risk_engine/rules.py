"""Individual deterministic risk rules.

Each rule takes a RiskContext and returns a RiskCheckResult when it FAILS,
or None when it passes. Rules must be pure functions: no I/O, no randomness,
no AI calls. This is what makes them independently unit-testable and safe
to run on every order without surprises.
"""

from __future__ import annotations

from risk_engine.types import RiskCheckResult, RiskContext

SUPPORTED_EXCHANGES = {"NSE"}
SUPPORTED_PRODUCTS = {"DELIVERY"}


def check_kill_switch(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.trading_kill_switch_active:
        return RiskCheckResult(
            allowed=False,
            code="TRADING_KILL_SWITCH_ACTIVE",
            message="Trading is currently disabled by the kill switch in Settings.",
            requires_override=False,
        )
    return None


def check_daily_loss_limit(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.day_realized_and_unrealized_pnl <= -abs(ctx.limits.daily_loss_limit):
        return RiskCheckResult(
            allowed=False,
            code="DAILY_LOSS_LIMIT_EXCEEDED",
            message=(
                f"Today's loss of {abs(ctx.day_realized_and_unrealized_pnl):.2f} has "
                f"reached your configured daily loss limit of {ctx.limits.daily_loss_limit:.2f}."
            ),
            requires_override=False,
        )
    return None


def check_missing_fields(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.missing_fields:
        return RiskCheckResult(
            allowed=False,
            code="MISSING_FIELDS",
            message=(
                "Some required details are missing: "
                + ", ".join(ctx.order.missing_fields)
            ),
            requires_override=False,
        )
    return None


def check_ambiguous_symbol(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.ambiguous_symbol_candidates:
        return RiskCheckResult(
            allowed=False,
            code="AMBIGUOUS_SYMBOL",
            message=(
                "More than one company matches that name. Please choose the exact "
                "NSE symbol: " + ", ".join(ctx.order.ambiguous_symbol_candidates)
            ),
            requires_override=False,
        )
    return None


def check_symbol_resolved(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.symbol and not ctx.order.symbol_resolved:
        return RiskCheckResult(
            allowed=False,
            code="SYMBOL_NOT_FOUND",
            message=f"'{ctx.order.symbol}' is not a recognised NSE instrument.",
            requires_override=False,
        )
    return None


def check_unsupported_exchange(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.exchange and ctx.order.exchange not in SUPPORTED_EXCHANGES:
        return RiskCheckResult(
            allowed=False,
            code="UNSUPPORTED_EXCHANGE",
            message=f"Exchange '{ctx.order.exchange}' is not supported. Only NSE is supported.",
            requires_override=False,
        )
    return None


def check_unsupported_product(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.product and ctx.order.product not in SUPPORTED_PRODUCTS:
        return RiskCheckResult(
            allowed=False,
            code="UNSUPPORTED_PRODUCT",
            message=f"Product '{ctx.order.product}' is not supported. Only DELIVERY is supported.",
            requires_override=False,
        )
    return None


def check_invalid_price(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.order_type == "LIMIT":
        if ctx.order.limit_price is None or ctx.order.limit_price <= 0:
            return RiskCheckResult(
                allowed=False,
                code="INVALID_PRICE",
                message="A valid positive limit price is required for LIMIT orders.",
                requires_override=False,
            )
    return None


def check_max_quantity(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.quantity is not None and ctx.order.quantity > ctx.limits.max_quantity:
        return RiskCheckResult(
            allowed=False,
            code="MAX_QUANTITY_EXCEEDED",
            message=(
                f"Quantity {ctx.order.quantity} exceeds your configured maximum of "
                f"{ctx.limits.max_quantity}."
            ),
            requires_override=False,
        )
    if ctx.order.quantity is not None and ctx.order.quantity <= 0:
        return RiskCheckResult(
            allowed=False,
            code="MAX_QUANTITY_EXCEEDED",
            message="Quantity must be greater than zero.",
            requires_override=False,
        )
    return None


def _reference_price(ctx: RiskContext) -> float | None:
    if ctx.order.order_type == "LIMIT" and ctx.order.limit_price:
        return ctx.order.limit_price
    return ctx.market_price


def check_order_value_limit(ctx: RiskContext) -> RiskCheckResult | None:
    price = _reference_price(ctx)
    if price is None or ctx.order.quantity is None:
        return None
    order_value = price * ctx.order.quantity
    if order_value > ctx.limits.max_order_value:
        return RiskCheckResult(
            allowed=False,
            code="ORDER_VALUE_LIMIT_EXCEEDED",
            message=(
                f"Order value of {order_value:.2f} exceeds your configured limit of "
                f"{ctx.limits.max_order_value:.2f}."
            ),
            requires_override=False,
        )
    return None


def check_insufficient_balance(ctx: RiskContext) -> RiskCheckResult | None:
    if ctx.order.side != "BUY":
        return None
    price = _reference_price(ctx)
    if price is None or ctx.order.quantity is None:
        return None
    order_value = price * ctx.order.quantity
    if order_value > ctx.available_balance:
        return RiskCheckResult(
            allowed=False,
            code="INSUFFICIENT_BALANCE",
            message=(
                f"Order value of {order_value:.2f} exceeds your available paper "
                f"balance of {ctx.available_balance:.2f}."
            ),
            requires_override=False,
        )
    return None


def check_price_deviation(ctx: RiskContext) -> RiskCheckResult | None:
    if (
        ctx.order.order_type != "LIMIT"
        or ctx.order.limit_price is None
        or ctx.market_price is None
        or ctx.market_price == 0
    ):
        return None
    deviation_pct = abs(ctx.order.limit_price - ctx.market_price) / ctx.market_price * 100
    if deviation_pct > ctx.limits.max_price_deviation_pct:
        return RiskCheckResult(
            allowed=False,
            code="PRICE_DEVIATION_TOO_HIGH",
            message=(
                f"Limit price {ctx.order.limit_price:.2f} deviates {deviation_pct:.1f}% "
                f"from the current market price {ctx.market_price:.2f}, which exceeds "
                f"the allowed {ctx.limits.max_price_deviation_pct:.1f}%."
            ),
            requires_override=True,
        )
    return None


def check_duplicate_order(ctx: RiskContext) -> RiskCheckResult | None:
    if not ctx.order.symbol or ctx.order.quantity is None:
        return None
    window = ctx.limits.duplicate_order_window_seconds
    for recent in ctx.recent_orders:
        age_seconds = (ctx.now - recent.placed_at).total_seconds()
        if (
            0 <= age_seconds <= window
            and recent.symbol == ctx.order.symbol
            and recent.side == ctx.order.side
            and recent.quantity == ctx.order.quantity
            and recent.order_type == ctx.order.order_type
            and recent.limit_price == ctx.order.limit_price
        ):
            return RiskCheckResult(
                allowed=False,
                code="DUPLICATE_ORDER",
                message=(
                    "An identical order was placed "
                    f"{age_seconds:.0f}s ago. Confirm again if this is intentional."
                ),
                requires_override=True,
            )
    return None


def check_market_open(ctx: RiskContext) -> RiskCheckResult | None:
    if not ctx.market_open:
        return RiskCheckResult(
            allowed=False,
            code="MARKET_CLOSED",
            message="The simulated market is currently closed. Orders will queue for the next session.",
            requires_override=True,
        )
    return None


# Order matters: the first failing rule is returned to the user.
ALL_RULES = [
    check_kill_switch,
    check_daily_loss_limit,
    check_missing_fields,
    check_ambiguous_symbol,
    check_symbol_resolved,
    check_unsupported_exchange,
    check_unsupported_product,
    check_invalid_price,
    check_max_quantity,
    check_order_value_limit,
    check_insufficient_balance,
    check_price_deviation,
    check_duplicate_order,
    check_market_open,
]
