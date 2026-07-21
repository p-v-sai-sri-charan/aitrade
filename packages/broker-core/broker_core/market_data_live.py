"""Live-ish NSE quotes from Yahoo Finance's public, unauthenticated chart
endpoint (NSE symbols are queried as `SYMBOL.NS`, e.g. `RELIANCE.NS`).

This is an unofficial endpoint intended for personal/non-commercial use,
not a licensed market-data feed -- it is a free, no-API-key seam to make
the app work with real prices for any listed NSE symbol out of the box.
For a real deployment, swap this for a licensed vendor or your broker's
market-data API behind the same `MarketDataProvider` protocol.

Like the live instrument repository, this NEVER raises on failure -- a
network error or unexpected response just means `get_quote` returns None,
which the rest of the app already treats as "no market data available"
(the paper broker rejects the order with a clear reason instead of
executing on stale/missing data).
"""

from __future__ import annotations

import logging
import time

import httpx

from broker_core.market_data import Quote

logger = logging.getLogger("broker_core.market_data_live")

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS"

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}


class YahooFinanceMarketDataProvider:
    source = "yahoo"

    def __init__(self, cache_ttl_seconds: float = 5.0, timeout: float = 8.0) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout = timeout
        # symbol -> (fetched_at_monotonic, Quote)
        self._cache: dict[str, tuple[float, Quote]] = {}

    async def get_quote(self, symbol: str, company_name: str = "") -> Quote | None:
        symbol = symbol.upper().strip()
        cached = self._cache.get(symbol)
        now = time.monotonic()
        if cached and now - cached[0] < self.cache_ttl_seconds:
            return cached[1]

        quote = await self._fetch(symbol, company_name)
        if quote is not None:
            self._cache[symbol] = (now, quote)
            return quote

        # Serve a stale cached quote rather than nothing if the live fetch
        # just failed (e.g. transient rate limit) but we have something.
        if cached:
            return cached[1]
        return None

    async def _fetch(self, symbol: str, company_name: str) -> Quote | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=_BROWSER_HEADERS) as client:
                response = await client.get(YAHOO_CHART_URL.format(symbol=symbol))
                response.raise_for_status()
                data = response.json()

            result = (data.get("chart") or {}).get("result") or []
            if not result:
                return None
            meta = result[0].get("meta") or {}
            last_price = meta.get("regularMarketPrice")
            previous_close = meta.get("previousClose") or meta.get("chartPreviousClose")
            if last_price is None or previous_close in (None, 0):
                return None

            resolved_name = company_name or meta.get("longName") or meta.get("shortName") or symbol
            change_pct = round((last_price - previous_close) / previous_close * 100, 2)
            return Quote(
                symbol=symbol,
                company_name=resolved_name,
                last_price=round(float(last_price), 2),
                previous_close=round(float(previous_close), 2),
                change_pct=change_pct,
            )
        except Exception as exc:  # noqa: BLE001 -- external API, never let it crash order flow
            logger.warning("Live quote fetch failed for %s: %s", symbol, exc)
            return None
