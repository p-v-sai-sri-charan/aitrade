"""Backend-side instrument resolution. Deterministic; never guesses.

Wraps `broker_core.resolve_instrument` -- kept as a thin, named seam so a
real NSE instrument master lookup can replace the seeded list later without
touching any router.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from broker_core.instruments import Instrument, resolve_instrument


@dataclass(frozen=True)
class ResolvedInstrument:
    instrument: Optional[Instrument]
    ambiguous_candidates: list[Instrument]

    @property
    def is_resolved(self) -> bool:
        return self.instrument is not None


def resolve_symbol(query: str) -> ResolvedInstrument:
    result = resolve_instrument(query)
    return ResolvedInstrument(instrument=result.instrument, ambiguous_candidates=result.candidates)
