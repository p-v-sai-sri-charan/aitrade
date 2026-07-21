"""Persistence seam for the paper broker.

`PaperBroker` never talks to a database directly -- it operates on a
`BrokerStore`. The API wires a SQLAlchemy-backed store; tests and
standalone usage can use `InMemoryBrokerStore`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from broker_core.models import OrderRecord, PositionRecord


class BrokerStore(Protocol):
    def get_balance(self) -> float: ...
    def set_balance(self, value: float) -> None: ...

    def get_realized_pnl_today(self) -> float: ...
    def add_realized_pnl_today(self, delta: float) -> None: ...

    def list_positions(self) -> list[PositionRecord]: ...
    def get_position(self, symbol: str) -> PositionRecord | None: ...
    def upsert_position(self, position: PositionRecord) -> None: ...
    def remove_position(self, symbol: str) -> None: ...

    def add_order(self, order: OrderRecord) -> None: ...
    def update_order(self, order: OrderRecord) -> None: ...
    def get_order(self, order_id: str) -> OrderRecord | None: ...
    def list_orders(self) -> list[OrderRecord]: ...
    def list_recent_orders(self, since: datetime) -> list[OrderRecord]: ...


class InMemoryBrokerStore:
    """Reference implementation used for tests and standalone/demo usage."""

    def __init__(self, starting_balance: float = 1_000_000.0) -> None:
        self._balance = starting_balance
        self._realized_pnl_today = 0.0
        self._positions: dict[str, PositionRecord] = {}
        self._orders: dict[str, OrderRecord] = {}

    def get_balance(self) -> float:
        return self._balance

    def set_balance(self, value: float) -> None:
        self._balance = value

    def get_realized_pnl_today(self) -> float:
        return self._realized_pnl_today

    def add_realized_pnl_today(self, delta: float) -> None:
        self._realized_pnl_today += delta

    def list_positions(self) -> list[PositionRecord]:
        return list(self._positions.values())

    def get_position(self, symbol: str) -> PositionRecord | None:
        return self._positions.get(symbol)

    def upsert_position(self, position: PositionRecord) -> None:
        self._positions[position.symbol] = position

    def remove_position(self, symbol: str) -> None:
        self._positions.pop(symbol, None)

    def add_order(self, order: OrderRecord) -> None:
        self._orders[order.id] = order

    def update_order(self, order: OrderRecord) -> None:
        self._orders[order.id] = order

    def get_order(self, order_id: str) -> OrderRecord | None:
        return self._orders.get(order_id)

    def list_orders(self) -> list[OrderRecord]:
        return sorted(self._orders.values(), key=lambda o: o.created_at, reverse=True)

    def list_recent_orders(self, since: datetime) -> list[OrderRecord]:
        return [o for o in self._orders.values() if o.created_at >= since]
