"""MarketDataProvider -- the seam for plugging in a real price feed instead
of the seeded/jittered mock prices.

Selected via `MARKET_DATA_PROVIDER` (mock | yahoo) through
`create_market_data_provider`, wired in `apps/api/app/deps.py`. Nothing
outside this package should import a specific implementation directly --
`PaperBroker` only ever depends on this Protocol.
"""

from __future__ import annotations

from typing import Protocol

from broker_core.market_data import Quote, SeededMarketDataProvider


class MarketDataProvider(Protocol):
    source: str

    async def get_quote(self, symbol: str, company_name: str = "") -> Quote | None: ...


SUPPORTED_MARKET_DATA_PROVIDERS = {"mock", "yahoo"}


def create_market_data_provider(provider: str = "mock", **kwargs: object) -> MarketDataProvider:
    provider = (provider or "mock").strip().lower()
    if provider not in SUPPORTED_MARKET_DATA_PROVIDERS:
        raise ValueError(
            f"Unknown MARKET_DATA_PROVIDER '{provider}'. Supported: {sorted(SUPPORTED_MARKET_DATA_PROVIDERS)}"
        )
    if provider == "mock":
        return SeededMarketDataProvider()

    from broker_core.market_data_live import YahooFinanceMarketDataProvider

    return YahooFinanceMarketDataProvider(**kwargs)  # type: ignore[arg-type]
