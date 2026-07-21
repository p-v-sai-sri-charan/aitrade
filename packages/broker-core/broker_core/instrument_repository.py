"""InstrumentRepository -- the seam for "auto-fetch the full NSE instrument
universe" instead of the small seeded/curated list.

Two implementations ship here (the seeded default) and in
`instrument_repository_live.py` (a live NSE-fetched universe). Selected via
`INSTRUMENT_SOURCE` (seeded | nse) through `create_instrument_repository`,
wired in `apps/api/app/deps.py`. Both implementations share the same
ambiguity-safe matching logic (`resolve_against` in `instruments.py`) so
switching sources never changes matching *behavior*, only the size of the
universe being matched against.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from broker_core.instruments import (
    INSTRUMENTS,
    Instrument,
    ResolveResult,
    get_instrument,
    resolve_against,
    search_against,
)


class InstrumentRepository(Protocol):
    source: str
    last_refreshed_at: datetime | None

    async def resolve(self, query: str) -> ResolveResult: ...
    async def get(self, symbol: str) -> Instrument | None: ...
    async def search(self, query: str, limit: int = 20) -> list[Instrument]: ...
    async def all_instruments(self) -> list[Instrument]: ...
    async def refresh(self) -> int:
        """Force a refresh from the underlying source. Returns the resulting
        instrument count. Must never raise -- failures should log and keep
        whatever instrument list was already loaded."""
        ...


class SeededInstrumentRepository:
    """Wraps the small, hand-curated offline instrument list. Always
    available, needs no network -- the default and the fallback for
    `NSEInstrumentRepository`.
    """

    source = "seeded"
    last_refreshed_at: datetime | None = None

    async def resolve(self, query: str) -> ResolveResult:
        return resolve_against(query, INSTRUMENTS, {i.symbol: i for i in INSTRUMENTS})

    async def get(self, symbol: str) -> Instrument | None:
        return get_instrument(symbol)

    async def search(self, query: str, limit: int = 20) -> list[Instrument]:
        return search_against(query, INSTRUMENTS, limit)

    async def all_instruments(self) -> list[Instrument]:
        return list(INSTRUMENTS)

    async def refresh(self) -> int:
        return len(INSTRUMENTS)


SUPPORTED_INSTRUMENT_SOURCES = {"seeded", "nse"}


def create_instrument_repository(source: str = "seeded", **kwargs: object) -> InstrumentRepository:
    source = (source or "seeded").strip().lower()
    if source not in SUPPORTED_INSTRUMENT_SOURCES:
        raise ValueError(
            f"Unknown INSTRUMENT_SOURCE '{source}'. Supported: {sorted(SUPPORTED_INSTRUMENT_SOURCES)}"
        )
    if source == "seeded":
        return SeededInstrumentRepository()

    from broker_core.instrument_repository_live import NSEInstrumentRepository

    return NSEInstrumentRepository(**kwargs)  # type: ignore[arg-type]
