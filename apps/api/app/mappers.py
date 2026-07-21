"""Converts broker-core dataclasses into API response schemas."""

from __future__ import annotations

from broker_core import market_data
from broker_core.models import OrderRecord, PortfolioSnapshot, PositionRecord
from broker_core.market_data import Quote as BrokerQuote
from app.schemas import OrderSchema, PortfolioSchema, PositionSchema, QuoteSchema
from datetime import datetime, timezone


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


def position_to_schema(position: PositionRecord) -> PositionSchema:
    current_price = market_data.get_last_price(position.symbol) or position.average_price
    unrealized_pnl = (current_price - position.average_price) * position.quantity
    invested = position.average_price * position.quantity
    unrealized_pnl_pct = (unrealized_pnl / invested * 100) if invested else 0.0
    return PositionSchema(
        symbol=position.symbol,
        companyName=position.company_name,
        quantity=position.quantity,
        averagePrice=position.average_price,
        currentPrice=round(current_price, 2),
        unrealizedPnl=round(unrealized_pnl, 2),
        unrealizedPnlPct=round(unrealized_pnl_pct, 2),
        realizedPnl=round(position.realized_pnl, 2),
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
