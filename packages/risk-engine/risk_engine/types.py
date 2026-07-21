"""Pure data types for the risk engine. No network, no DB, no AI calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

RiskCode = Literal[
    "ORDER_VALUE_LIMIT_EXCEEDED",
    "MAX_QUANTITY_EXCEEDED",
    "INSUFFICIENT_BALANCE",
    "DUPLICATE_ORDER",
    "INVALID_PRICE",
    "PRICE_DEVIATION_TOO_HIGH",
    "MISSING_FIELDS",
    "AMBIGUOUS_SYMBOL",
    "UNSUPPORTED_EXCHANGE",
    "UNSUPPORTED_PRODUCT",
    "DAILY_LOSS_LIMIT_EXCEEDED",
    "TRADING_KILL_SWITCH_ACTIVE",
    "SYMBOL_NOT_FOUND",
    "MARKET_CLOSED",
]


@dataclass(frozen=True)
class RiskCheckResult:
    allowed: bool
    code: str  # RiskCode or "OK"
    message: str
    requires_override: bool = False

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "message": self.message,
            "requiresOverride": self.requires_override,
        }


@dataclass(frozen=True)
class RiskLimits:
    max_order_value: float = 200_000
    max_quantity: int = 5_000
    max_price_deviation_pct: float = 5.0
    daily_loss_limit: float = 25_000
    duplicate_order_window_seconds: int = 10


@dataclass(frozen=True)
class RecentOrderFingerprint:
    """A minimal record of a recently placed order, used for duplicate detection."""

    symbol: str
    side: str
    quantity: int
    order_type: str
    limit_price: Optional[float]
    placed_at: datetime


@dataclass(frozen=True)
class OrderRequestContext:
    exchange: Optional[str]
    symbol: Optional[str]
    side: Optional[str]
    quantity: Optional[int]
    order_type: Optional[str]
    limit_price: Optional[float]
    product: Optional[str]
    validity: Optional[str]
    missing_fields: list[str] = field(default_factory=list)
    ambiguous_symbol_candidates: list[str] = field(default_factory=list)
    symbol_resolved: bool = True


@dataclass(frozen=True)
class RiskContext:
    order: OrderRequestContext
    limits: RiskLimits
    available_balance: float
    market_price: Optional[float]
    day_realized_and_unrealized_pnl: float
    recent_orders: list[RecentOrderFingerprint]
    now: datetime
    trading_kill_switch_active: bool = False
    market_open: bool = True
