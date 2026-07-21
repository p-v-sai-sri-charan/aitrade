"""Pydantic schemas -- the backend's OWN, independent validation of every
shape that crosses the API boundary. AI provider output is re-validated
against `TradeIntentSchema` here; it is never trusted as-is.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(snake: str) -> str:
    first, *rest = snake.split("_")
    return first + "".join(word.capitalize() for word in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)


# ---- Trade intent ----

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
OrderStatus = Literal["PENDING", "FILLED", "PARTIALLY_FILLED", "REJECTED", "CANCELLED"]


class TradeIntentInputSchema(CamelModel):
    transcript: str = Field(min_length=1, max_length=500)
    detected_language: Optional[CommandLanguage] = None
    conversation_context: dict[str, Any] = Field(default_factory=dict)


class TradeIntentSchema(CamelModel):
    intent: TradeIntentType
    language: CommandLanguage
    confidence: float = Field(ge=0, le=1)
    missing_fields: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    exchange: Optional[Literal["NSE"]] = None
    symbol: Optional[str] = None
    side: Optional[OrderSide] = None
    quantity: Optional[int] = Field(default=None, gt=0)
    order_type: Optional[OrderType] = None
    limit_price: Optional[float] = Field(default=None, gt=0)
    product: Optional[OrderProduct] = None
    validity: Optional[OrderValidity] = None
    ambiguous_symbol_candidates: list[str] = Field(default_factory=list)
    order_id: Optional[str] = None


class IntentParseResponse(CamelModel):
    intent: TradeIntentSchema
    provider: str


# ---- Orders ----


class OrderRequestSchema(CamelModel):
    exchange: Literal["NSE"]
    symbol: str
    side: OrderSide
    quantity: int = Field(gt=0)
    order_type: OrderType
    limit_price: Optional[float] = Field(default=None, gt=0)
    product: OrderProduct = "DELIVERY"
    validity: OrderValidity = "DAY"


class RiskCheckResultSchema(CamelModel):
    allowed: bool
    code: str
    message: str
    requires_override: bool = False


class OrderPreviewSchema(CamelModel):
    preview_id: str
    request: OrderRequestSchema
    company_name: str
    estimated_price: float
    estimated_value: float
    estimated_brokerage: float
    estimated_taxes: float
    estimated_total: float
    risk_check: RiskCheckResultSchema
    expires_at: datetime


class OrderConfirmRequestSchema(CamelModel):
    preview_id: str
    idempotency_key: str = Field(min_length=8, max_length=128)


class OrderSchema(CamelModel):
    id: str
    exchange: str
    symbol: str
    company_name: str
    side: OrderSide
    quantity: int
    filled_quantity: int
    order_type: OrderType
    limit_price: Optional[float] = None
    average_fill_price: Optional[float] = None
    product: OrderProduct
    validity: OrderValidity
    status: OrderStatus
    brokerage: float
    taxes: float
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---- Portfolio / positions / quotes ----


class PositionSchema(CamelModel):
    symbol: str
    company_name: str
    quantity: int
    average_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float


class PortfolioSchema(CamelModel):
    available_balance: float
    used_margin: float
    portfolio_value: float
    total_invested: float
    day_pnl: float
    day_pnl_pct: float
    total_pnl: float
    positions: list[PositionSchema]


class QuoteSchema(CamelModel):
    symbol: str
    company_name: str
    last_price: float
    previous_close: float
    change_pct: float
    updated_at: datetime


# ---- Instruments ----


class InstrumentSchema(CamelModel):
    symbol: str
    company_name: str
    exchange: Literal["NSE"]


class InstrumentStatusSchema(CamelModel):
    source: str
    instrument_count: int
    last_refreshed_at: Optional[datetime] = None


# ---- Audit log ----


class AuditLogEntrySchema(CamelModel):
    id: str
    timestamp: datetime
    original_transcript: Optional[str] = None
    detected_language: Optional[str] = None
    parsed_intent: Optional[dict[str, Any]] = None
    ai_provider: Optional[str] = None
    validation_valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    risk_check: Optional[dict[str, Any]] = None
    user_confirmed: Optional[bool] = None
    order_response_summary: Optional[str] = None
    order_id: Optional[str] = None


# ---- Settings ----

AIProviderName = Literal["mock", "anthropic", "openai", "gemini", "local", "ollama"]
LanguagePreference = Literal["hi-IN", "en-IN", "hinglish", "auto"]


class RiskLimitsSchema(CamelModel):
    max_order_value: float = Field(gt=0)
    max_quantity: int = Field(gt=0)
    max_price_deviation_pct: float = Field(gt=0)
    daily_loss_limit: float = Field(gt=0)


class SettingsSchema(CamelModel):
    ai_provider: AIProviderName
    language_preference: LanguagePreference
    voice_output_enabled: bool
    risk_limits: RiskLimitsSchema
    trading_kill_switch: bool


class SettingsUpdateSchema(CamelModel):
    ai_provider: Optional[AIProviderName] = None
    language_preference: Optional[LanguagePreference] = None
    voice_output_enabled: Optional[bool] = None
    risk_limits: Optional[RiskLimitsSchema] = None
    trading_kill_switch: Optional[bool] = None
