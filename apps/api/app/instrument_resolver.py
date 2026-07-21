"""Backend-side instrument resolution. Deterministic; never guesses.

Delegates to whichever `InstrumentRepository` is configured (the seeded
~20-stock list, or the full live-fetched NSE universe) -- callers never
need to know which source is active.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from broker_core.instrument_repository import InstrumentRepository
from broker_core.instruments import Instrument


@dataclass(frozen=True)
class ResolvedInstrument:
    instrument: Optional[Instrument]
    ambiguous_candidates: list[Instrument]

    @property
    def is_resolved(self) -> bool:
        return self.instrument is not None


async def resolve_symbol(query: str, repository: InstrumentRepository) -> ResolvedInstrument:
    result = await repository.resolve(query)
    return ResolvedInstrument(instrument=result.instrument, ambiguous_candidates=result.candidates)
