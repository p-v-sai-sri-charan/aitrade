"""A realistic simulated NSE paper broker.

Implements `BrokerAdapter`. Market orders fill immediately against the
simulated last-traded price plus configurable slippage; limit orders fill
immediately if the market already satisfies the limit, otherwise stay
PENDING. Brokerage is a flat fee; taxes approximate STT (sell side) and GST
on brokerage. This is a simplification for demo/education purposes, not a
real settlement engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from broker_core import market_data
from broker_core.models import (
    OrderRecord,
    OrderRequest,
    PortfolioSnapshot,
    PositionRecord,
)
from broker_core.pricing import PaperBrokerConfig, compute_charges
from broker_core.store import BrokerStore


class OrderNotFoundError(Exception):
    pass


class OrderNotCancellableError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PaperBroker:
    """Implements the `BrokerAdapter` protocol (structurally, via duck typing)."""

    def __init__(self, store: BrokerStore, config: PaperBrokerConfig | None = None) -> None:
        self.store = store
        self.config = config or PaperBrokerConfig()

    async def get_quote(self, symbol: str) -> market_data.Quote | None:
        return market_data.get_quote(symbol)

    def _execution_price(self, order: OrderRequest, last_price: float) -> float | None:
        """Return the fill price if the order fills now, else None (stays PENDING)."""
        if order.order_type == "MARKET":
            slippage = last_price * (self.config.slippage_bps / 10_000)
            return last_price + slippage if order.side == "BUY" else last_price - slippage

        # LIMIT order
        assert order.limit_price is not None
        if order.side == "BUY" and last_price <= order.limit_price:
            return min(last_price, order.limit_price)
        if order.side == "SELL" and last_price >= order.limit_price:
            return max(last_price, order.limit_price)
        return None

    def _charges(self, side: str, value: float) -> tuple[float, float]:
        return compute_charges(side, value, self.config)

    async def place_order(self, order: OrderRequest) -> OrderRecord:
        now = _now()
        order_id = str(uuid.uuid4())

        quote = market_data.get_quote(order.symbol)
        if quote is None:
            record = OrderRecord(
                id=order_id,
                exchange=order.exchange,
                symbol=order.symbol,
                company_name=order.company_name,
                side=order.side,
                quantity=order.quantity,
                filled_quantity=0,
                order_type=order.order_type,
                limit_price=order.limit_price,
                average_fill_price=None,
                product=order.product,
                validity=order.validity,
                status="REJECTED",
                brokerage=0.0,
                taxes=0.0,
                rejection_reason="No market data available for this instrument.",
                created_at=now,
                updated_at=now,
            )
            self.store.add_order(record)
            return record

        if order.side == "SELL":
            held = self.store.get_position(order.symbol)
            if held is None or held.quantity < order.quantity:
                record = OrderRecord(
                    id=order_id,
                    exchange=order.exchange,
                    symbol=order.symbol,
                    company_name=order.company_name,
                    side=order.side,
                    quantity=order.quantity,
                    filled_quantity=0,
                    order_type=order.order_type,
                    limit_price=order.limit_price,
                    average_fill_price=None,
                    product=order.product,
                    validity=order.validity,
                    status="REJECTED",
                    brokerage=0.0,
                    taxes=0.0,
                    rejection_reason="Insufficient holdings for this sell order.",
                    created_at=now,
                    updated_at=now,
                )
                self.store.add_order(record)
                return record

        fill_price = self._execution_price(order, quote.last_price)

        if fill_price is None:
            record = OrderRecord(
                id=order_id,
                exchange=order.exchange,
                symbol=order.symbol,
                company_name=order.company_name,
                side=order.side,
                quantity=order.quantity,
                filled_quantity=0,
                order_type=order.order_type,
                limit_price=order.limit_price,
                average_fill_price=None,
                product=order.product,
                validity=order.validity,
                status="PENDING",
                brokerage=0.0,
                taxes=0.0,
                rejection_reason=None,
                created_at=now,
                updated_at=now,
            )
            self.store.add_order(record)
            return record

        value = round(fill_price * order.quantity, 2)
        brokerage, taxes = self._charges(order.side, value)

        if order.side == "BUY":
            total_cost = value + brokerage + taxes
            if total_cost > self.store.get_balance():
                record = OrderRecord(
                    id=order_id,
                    exchange=order.exchange,
                    symbol=order.symbol,
                    company_name=order.company_name,
                    side=order.side,
                    quantity=order.quantity,
                    filled_quantity=0,
                    order_type=order.order_type,
                    limit_price=order.limit_price,
                    average_fill_price=None,
                    product=order.product,
                    validity=order.validity,
                    status="REJECTED",
                    brokerage=0.0,
                    taxes=0.0,
                    rejection_reason="Insufficient paper balance at execution time.",
                    created_at=now,
                    updated_at=now,
                )
                self.store.add_order(record)
                return record

            self.store.set_balance(self.store.get_balance() - total_cost)
            existing = self.store.get_position(order.symbol)
            if existing is None:
                self.store.upsert_position(
                    PositionRecord(
                        symbol=order.symbol,
                        company_name=order.company_name,
                        quantity=order.quantity,
                        average_price=fill_price,
                    )
                )
            else:
                new_qty = existing.quantity + order.quantity
                new_avg = (
                    existing.quantity * existing.average_price + order.quantity * fill_price
                ) / new_qty
                self.store.upsert_position(
                    PositionRecord(
                        symbol=order.symbol,
                        company_name=order.company_name,
                        quantity=new_qty,
                        average_price=round(new_avg, 4),
                        realized_pnl=existing.realized_pnl,
                    )
                )
        else:  # SELL
            proceeds = value - brokerage - taxes
            self.store.set_balance(self.store.get_balance() + proceeds)
            existing = self.store.get_position(order.symbol)
            assert existing is not None
            realized = (fill_price - existing.average_price) * order.quantity
            self.store.add_realized_pnl_today(realized)
            remaining_qty = existing.quantity - order.quantity
            if remaining_qty == 0:
                self.store.remove_position(order.symbol)
            else:
                self.store.upsert_position(
                    PositionRecord(
                        symbol=order.symbol,
                        company_name=order.company_name,
                        quantity=remaining_qty,
                        average_price=existing.average_price,
                        realized_pnl=existing.realized_pnl + realized,
                    )
                )

        record = OrderRecord(
            id=order_id,
            exchange=order.exchange,
            symbol=order.symbol,
            company_name=order.company_name,
            side=order.side,
            quantity=order.quantity,
            filled_quantity=order.quantity,
            order_type=order.order_type,
            limit_price=order.limit_price,
            average_fill_price=fill_price,
            product=order.product,
            validity=order.validity,
            status="FILLED",
            brokerage=brokerage,
            taxes=taxes,
            rejection_reason=None,
            created_at=now,
            updated_at=now,
        )
        self.store.add_order(record)
        return record

    async def cancel_order(self, order_id: str) -> OrderRecord:
        order = self.store.get_order(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        if order.status != "PENDING":
            raise OrderNotCancellableError(
                f"Order {order_id} is {order.status} and cannot be cancelled."
            )
        order.status = "CANCELLED"
        order.updated_at = _now()
        self.store.update_order(order)
        return order

    async def get_orders(self) -> list[OrderRecord]:
        return self.store.list_orders()

    async def get_positions(self) -> list[PositionRecord]:
        return self.store.list_positions()

    async def get_portfolio(self) -> PortfolioSnapshot:
        positions = self.store.list_positions()
        total_invested = sum(p.quantity * p.average_price for p in positions)
        market_value = 0.0
        unrealized_pnl = 0.0
        for p in positions:
            last_price = market_data.get_last_price(p.symbol) or p.average_price
            market_value += p.quantity * last_price
            unrealized_pnl += (last_price - p.average_price) * p.quantity

        realized_today = self.store.get_realized_pnl_today()
        day_pnl = realized_today + unrealized_pnl
        day_pnl_pct = (day_pnl / total_invested * 100) if total_invested else 0.0
        balance = self.store.get_balance()

        return PortfolioSnapshot(
            available_balance=round(balance, 2),
            used_margin=0.0,
            portfolio_value=round(balance + market_value, 2),
            total_invested=round(total_invested, 2),
            day_pnl=round(day_pnl, 2),
            day_pnl_pct=round(day_pnl_pct, 2),
            total_pnl=round(day_pnl, 2),
            positions=positions,
        )
