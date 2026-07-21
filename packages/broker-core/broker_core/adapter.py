"""BrokerAdapter interface.

Any real NSE broker integration (or another paper broker implementation)
should implement this Protocol. Nothing outside this package should import
`PaperBroker` directly -- depend on `BrokerAdapter` instead so a real
adapter is a drop-in replacement.
"""

from __future__ import annotations

from typing import Protocol

from broker_core.market_data import Quote
from broker_core.models import EnrichedPosition, OrderRecord, OrderRequest, PortfolioSnapshot


class BrokerAdapter(Protocol):
    async def get_quote(self, symbol: str) -> Quote | None: ...
    async def place_order(self, order: OrderRequest) -> OrderRecord: ...
    async def cancel_order(self, order_id: str) -> OrderRecord: ...
    async def get_orders(self) -> list[OrderRecord]: ...
    async def get_positions(self) -> list[EnrichedPosition]: ...
    async def get_portfolio(self) -> PortfolioSnapshot: ...
