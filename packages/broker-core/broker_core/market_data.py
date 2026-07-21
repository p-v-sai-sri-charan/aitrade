"""Mocked/seeded market prices.

Deterministic per-symbol "previous close" seeds with a small time-bucketed
pseudo-random walk so quotes move slightly between calls without needing a
live feed. Swap this module for a real NSE market data adapter later --
`get_last_price` / `get_quote` is the seam.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from broker_core.instruments import get_instrument

SEED_PRICES: dict[str, float] = {
    "RELIANCE": 2955.50,
    "TCS": 3845.20,
    "TATAMOTORS": 985.40,
    "TATASTEEL": 168.75,
    "TATAPOWER": 412.30,
    "TATACONSUM": 1120.60,
    "INFY": 1585.90,
    "HDFCBANK": 1642.10,
    "ICICIBANK": 1198.45,
    "SBIN": 825.30,
    "ITC": 468.20,
    "HINDUNILVR": 2410.75,
    "BHARTIARTL": 1495.60,
    "WIPRO": 545.15,
    "LT": 3610.90,
    "AXISBANK": 1145.25,
    "KOTAKBANK": 1780.40,
    "MARUTI": 12850.00,
    "SUNPHARMA": 1745.30,
    "ONGC": 265.80,
}


@dataclass(frozen=True)
class Quote:
    symbol: str
    company_name: str
    last_price: float
    previous_close: float
    change_pct: float


def _time_bucket(seconds: int = 5) -> int:
    """Bucket "now" so repeated calls within `seconds` return the same jitter."""
    return int(time.time() // seconds)


def get_last_price(symbol: str) -> float | None:
    base = SEED_PRICES.get(symbol.upper())
    if base is None:
        return None
    rng = random.Random(f"{symbol.upper()}-{_time_bucket()}")
    jitter_pct = rng.uniform(-0.35, 0.35)
    return round(base * (1 + jitter_pct / 100), 2)


def get_quote(symbol: str) -> Quote | None:
    instrument = get_instrument(symbol)
    base = SEED_PRICES.get(symbol.upper())
    if instrument is None or base is None:
        return None
    last_price = get_last_price(symbol) or base
    change_pct = round((last_price - base) / base * 100, 2)
    return Quote(
        symbol=instrument.symbol,
        company_name=instrument.company_name,
        last_price=last_price,
        previous_close=base,
        change_pct=change_pct,
    )
