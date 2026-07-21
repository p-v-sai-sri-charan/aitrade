"""Types mirroring packages/shared-types/src/tradeIntent.ts.

These are the AI layer's OWN types -- the FastAPI app independently defines
and validates its own Pydantic schema for the same shape
(apps/api/app/schemas.py). Two independent validations are intentional: an
AI provider's output must never be trusted as-is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

TradeIntentType = Literal[
    "PLACE_ORDER",
    "CANCEL_ORDER",
    "VIEW_PORTFOLIO",
    "VIEW_ORDERS",
    "VIEW_POSITION",
    "UNKNOWN",
]
OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]
OrderProduct = Literal["DELIVERY"]
OrderValidity = Literal["DAY"]
CommandLanguage = Literal["hi-IN", "en-IN", "hinglish"]


@dataclass
class TradeIntent:
    intent: TradeIntentType
    language: CommandLanguage
    confidence: float
    missing_fields: list[str] = field(default_factory=list)
    requires_confirmation: bool = False
    exchange: Optional[Literal["NSE"]] = None
    symbol: Optional[str] = None
    side: Optional[OrderSide] = None
    quantity: Optional[int] = None
    order_type: Optional[OrderType] = None
    limit_price: Optional[float] = None
    product: Optional[OrderProduct] = None
    validity: Optional[OrderValidity] = None
    ambiguous_symbol_candidates: list[str] = field(default_factory=list)
    order_id: Optional[str] = None


@dataclass
class TradeIntentInput:
    transcript: str
    detected_language: Optional[CommandLanguage] = None
    conversation_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeIntentResult:
    intent: TradeIntent
    provider: str
    raw_provider_output: Optional[str] = None


@dataclass
class RiskExplanationInput:
    risk_code: str
    message: str
    language: CommandLanguage = "en-IN"
    order_context: dict[str, Any] = field(default_factory=dict)
