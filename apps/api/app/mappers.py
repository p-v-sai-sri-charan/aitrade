"""Converts broker-core dataclasses into API response schemas.

Pure, synchronous mapping only -- `EnrichedPosition` already carries its
current-price/unrealized-P&L snapshot (computed once inside
`PaperBroker.get_positions()`/`get_portfolio()` from whichever
`MarketDataProvider` is configured), so this layer never needs to make its
own market-data call.
"""

from __future__ import annotations

from datetime import datetime, timezone

from broker_core.market_data import Quote as BrokerQuote
from broker_core.models import EnrichedPosition, OrderRecord, PortfolioSnapshot
from app.schemas import OrderSchema, PortfolioSchema, PositionSchema, QuoteSchema


def order_to_schema(order: OrderRecord) -> OrderSchema:
    return OrderSchema(
        id=order.id,
        exchange=order.exchange,
        symbol=order.symbol,
        companyName=order.company_name,
        side=order.side,
        quantity=order.quantity,
        filledQuantity=order.filled_quantity,
        orderType=order.order_type,
        limitPrice=order.limit_price,
        averageFillPrice=order.average_fill_price,
        product=order.product,
        validity=order.validity,
        status=order.status,
        brokerage=order.brokerage,
        taxes=order.taxes,
        rejectionReason=order.rejection_reason,
        createdAt=order.created_at,
        updatedAt=order.updated_at,
    )


def position_to_schema(position: EnrichedPosition) -> PositionSchema:
    return PositionSchema(
        symbol=position.symbol,
        companyName=position.company_name,
        quantity=position.quantity,
        averagePrice=position.average_price,
        currentPrice=position.current_price,
        unrealizedPnl=position.unrealized_pnl,
        unrealizedPnlPct=position.unrealized_pnl_pct,
        realizedPnl=position.realized_pnl,
    )


def portfolio_to_schema(portfolio: PortfolioSnapshot) -> PortfolioSchema:
    return PortfolioSchema(
        availableBalance=portfolio.available_balance,
        usedMargin=portfolio.used_margin,
        portfolioValue=portfolio.portfolio_value,
        totalInvested=portfolio.total_invested,
        dayPnl=portfolio.day_pnl,
        dayPnlPct=portfolio.day_pnl_pct,
        totalPnl=portfolio.total_pnl,
        positions=[position_to_schema(p) for p in portfolio.positions],
    )


def quote_to_schema(quote: BrokerQuote) -> QuoteSchema:
    return QuoteSchema(
        symbol=quote.symbol,
        companyName=quote.company_name,
        lastPrice=quote.last_price,
        previousClose=quote.previous_close,
        changePct=quote.change_pct,
        updatedAt=datetime.now(timezone.utc),
    )
