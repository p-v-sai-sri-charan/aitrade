"""Fetches the full NSE-listed equity universe from NSE's public equity
list CSV instead of relying on the small seeded/curated list.

This talks to a real, unauthenticated NSE endpoint -- no API key needed --
but NSE's site is known to rate-limit or bot-challenge requests that don't
look like a real browser session, and the exact URL/format can change. This
implementation is deliberately defensive:

- Refresh failures are caught and logged, NEVER raised -- the repository
  keeps serving whatever instrument list it last had (or the seeded list,
  if it has never successfully refreshed).
- Refresh is lazy + cached: a background-ish refresh only happens when the
  cache is older than `cache_ttl_seconds`, and concurrent callers share one
  in-flight refresh via a lock.

For a production deployment, replace this with a licensed market-data
vendor's instrument master API -- this is a best-effort, free-tier seam,
not a guaranteed-uptime data source.
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging
from datetime import datetime, timezone

import httpx

from broker_core.instruments import INSTRUMENTS, Instrument, ResolveResult, resolve_against, search_against

logger = logging.getLogger("broker_core.instrument_repository_live")

NSE_EQUITY_LIST_URL = "https://nsearchives.nseindia.com/content/equity_list.csv"

# NSE blocks requests that don't look like a real browser.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/csv,*/*",
}


def parse_nse_equity_csv(csv_text: str) -> list[Instrument]:
    """Parses NSE's equity_list.csv format:
    SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE

    Only the "EQ" series (the main board, ordinary equity) is kept -- other
    series (debt instruments, SME board, etc.) are excluded to avoid noisy
    duplicate-looking symbols.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    instruments: list[Instrument] = []
    seen_symbols: set[str] = set()
    for row in reader:
        symbol = (row.get("SYMBOL") or "").strip().upper()
        company_name = (row.get(" NAME OF COMPANY") or row.get("NAME OF COMPANY") or "").strip()
        series = (row.get(" SERIES") or row.get("SERIES") or "").strip().upper()
        if not symbol or not company_name:
            continue
        if series and series != "EQ":
            continue
        if symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)
        instruments.append(Instrument(symbol=symbol, company_name=company_name, exchange="NSE"))
    return instruments


class NSEInstrumentRepository:
    """Live NSE equity universe with an in-memory TTL cache and a graceful
    fallback to the seeded list until (and unless) a refresh succeeds.
    """

    source = "nse"

    def __init__(self, cache_ttl_seconds: float = 86_400, timeout: float = 15.0) -> None:
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout = timeout
        self._instruments: list[Instrument] = list(INSTRUMENTS)
        self._by_symbol: dict[str, Instrument] = {i.symbol: i for i in self._instruments}
        self.last_refreshed_at: datetime | None = None
        self._lock = asyncio.Lock()

    def _is_stale(self) -> bool:
        if self.last_refreshed_at is None:
            return True
        age = (datetime.now(timezone.utc) - self.last_refreshed_at).total_seconds()
        return age > self.cache_ttl_seconds

    async def _ensure_fresh(self) -> None:
        if not self._is_stale():
            return
        async with self._lock:
            if not self._is_stale():
                return
            await self.refresh()

    async def refresh(self) -> int:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=_BROWSER_HEADERS) as client:
                response = await client.get(NSE_EQUITY_LIST_URL)
                response.raise_for_status()
                instruments = parse_nse_equity_csv(response.text)
            if instruments:
                self._instruments = instruments
                self._by_symbol = {i.symbol: i for i in instruments}
                self.last_refreshed_at = datetime.now(timezone.utc)
                logger.info("Refreshed NSE instrument universe: %d instruments", len(instruments))
            else:
                logger.warning("NSE instrument list refresh returned no rows; keeping previous list")
        except Exception as exc:  # noqa: BLE001 -- never let a flaky external fetch break the app
            logger.warning(
                "NSE instrument list refresh failed (%s); serving previous/seeded list of %d instruments",
                exc,
                len(self._instruments),
            )
        return len(self._instruments)

    async def get(self, symbol: str) -> Instrument | None:
        await self._ensure_fresh()
        return self._by_symbol.get(symbol.upper().strip())

    async def all_instruments(self) -> list[Instrument]:
        await self._ensure_fresh()
        return list(self._instruments)

    async def resolve(self, query: str) -> ResolveResult:
        await self._ensure_fresh()
        return resolve_against(query, self._instruments, self._by_symbol)

    async def search(self, query: str, limit: int = 20) -> list[Instrument]:
        await self._ensure_fresh()
        return search_against(query, self._instruments, limit)
