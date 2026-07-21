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
    symbol: str
    company_name: str
    quantity: int
    average_price: float
    realized_pnl: float = 0.0


@dataclass
class PortfolioSnapshot:
    available_balance: float
    used_margin: float
    portfolio_value: float
    total_invested: float
    day_pnl: float
    day_pnl_pct: float
    total_pnl: float
    positions: list[PositionRecord] = field(default_factory=list)
