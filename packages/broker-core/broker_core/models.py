from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]
OrderStatus = Literal["PENDING", "FILLED", "PARTIALLY_FILLED", "REJECTED", "CANCELLED"]
OrderProduct = Literal["DELIVERY"]
OrderValidity = Literal["DAY"]


@dataclass(frozen=True)
class OrderRequest:
    exchange: str
    symbol: str
    company_name: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    limit_price: Optional[float]
    product: OrderProduct
    validity: OrderValidity


@dataclass
class OrderRecord:
    id: str
    exchange: str
    symbol: str
    company_name: str
    side: OrderSide
    quantity: int
    filled_quantity: int
    order_type: OrderType
    limit_price: Optional[float]
    average_fill_price: Optional[float]
    product: OrderProduct
    validity: OrderValidity
    status: OrderStatus
    brokerage: float
    taxes: float
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class PositionRecord:
    """Persisted position state (what a `BrokerStore` reads/writes) --
    deliberately has no market-price-dependent fields, since those are a
    point-in-time computation, not stored state.
    """

    symbol: str
    company_name: str
    quantity: int
    average_price: float
    realized_pnl: float = 0.0


@dataclass
class EnrichedPosition:
    """A `PositionRecord` enriched with a current market price snapshot --
    what `PaperBroker.get_positions()` / `get_portfolio()` actually return.
    Computed fresh on every call from whichever `MarketDataProvider` is
    configured (seeded or live).
    """

    symbol: str
    company_name: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float


@dataclass
class PortfolioSnapshot:
    available_balance: float
    used_margin: float
    portfolio_value: float
    total_invested: float
    day_pnl: float
    day_pnl_pct: float
    total_pnl: float
    positions: list[EnrichedPosition] = field(default_factory=list)
