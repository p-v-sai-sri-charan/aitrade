"""Seeded NSE instrument master used for deterministic symbol resolution.

This intentionally ships a small, curated list rather than a live
instrument master API — good enough for paper trading demos, and the seam
(`INSTRUMENTS`, `resolve_instrument`) is where a real NSE instrument feed
would be plugged in later.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    symbol: str
    company_name: str
    exchange: str = "NSE"
    # Extra search terms, e.g. "TCS" -> "tata consultancy"
    aliases: tuple[str, ...] = ()


INSTRUMENTS: list[Instrument] = [
    Instrument("RELIANCE", "Reliance Industries Ltd", aliases=("reliance",)),
    Instrument("TCS", "Tata Consultancy Services Ltd", aliases=("tcs", "tata consultancy")),
    Instrument("TATAMOTORS", "Tata Motors Ltd", aliases=("tata motors",)),
    Instrument("TATASTEEL", "Tata Steel Ltd", aliases=("tata steel",)),
    Instrument("TATAPOWER", "Tata Power Company Ltd", aliases=("tata power",)),
    Instrument("TATACONSUM", "Tata Consumer Products Ltd", aliases=("tata consumer",)),
    Instrument("INFY", "Infosys Ltd", aliases=("infosys",)),
    Instrument("HDFCBANK", "HDFC Bank Ltd", aliases=("hdfc bank", "hdfc")),
    Instrument("ICICIBANK", "ICICI Bank Ltd", aliases=("icici bank", "icici")),
    Instrument("SBIN", "State Bank of India", aliases=("sbi", "state bank")),
    Instrument("ITC", "ITC Ltd", aliases=("itc",)),
    Instrument("HINDUNILVR", "Hindustan Unilever Ltd", aliases=("hul", "hindustan unilever")),
    Instrument("BHARTIARTL", "Bharti Airtel Ltd", aliases=("airtel", "bharti airtel")),
    Instrument("WIPRO", "Wipro Ltd", aliases=("wipro",)),
    Instrument("LT", "Larsen & Toubro Ltd", aliases=("l&t", "larsen", "larsen and toubro")),
    Instrument("AXISBANK", "Axis Bank Ltd", aliases=("axis bank", "axis")),
    Instrument("KOTAKBANK", "Kotak Mahindra Bank Ltd", aliases=("kotak", "kotak bank")),
    Instrument("MARUTI", "Maruti Suzuki India Ltd", aliases=("maruti", "maruti suzuki")),
    Instrument("SUNPHARMA", "Sun Pharmaceutical Industries Ltd", aliases=("sun pharma",)),
    Instrument("ONGC", "Oil and Natural Gas Corporation Ltd", aliases=("ongc",)),
]

_BY_SYMBOL = {i.symbol: i for i in INSTRUMENTS}


@dataclass(frozen=True)
class ResolveResult:
    instrument: Instrument | None
    candidates: list[Instrument]

    @property
    def is_resolved(self) -> bool:
        return self.instrument is not None

    @property
    def is_ambiguous(self) -> bool:
        return self.instrument is None and len(self.candidates) > 1

    @property
    def is_not_found(self) -> bool:
        return self.instrument is None and len(self.candidates) == 0


def get_instrument(symbol: str) -> Instrument | None:
    return _BY_SYMBOL.get(symbol.upper().strip())


def resolve_instrument(query: str) -> ResolveResult:
    """Resolve a free-text company/symbol reference to an exact NSE instrument.

    Never guesses when multiple instruments plausibly match (e.g. "Tata" ->
    5 different Tata group companies) -- callers must surface `candidates`
    to the user instead of picking one.
    """
    if not query:
        return ResolveResult(instrument=None, candidates=[])

    normalized = query.strip().lower()
    upper = query.strip().upper()

    # 1. Exact symbol match.
    if upper in _BY_SYMBOL:
        return ResolveResult(instrument=_BY_SYMBOL[upper], candidates=[])

    # 2. Exact company name match.
    exact_name_matches = [i for i in INSTRUMENTS if i.company_name.lower() == normalized]
    if len(exact_name_matches) == 1:
        return ResolveResult(instrument=exact_name_matches[0], candidates=[])

    # 3. Alias / substring match across company name + aliases.
    candidates = [
        i
        for i in INSTRUMENTS
        if normalized in i.company_name.lower()
        or any(normalized == alias or normalized in alias for alias in i.aliases)
    ]

    if len(candidates) == 1:
        return ResolveResult(instrument=candidates[0], candidates=[])
    if len(candidates) > 1:
        return ResolveResult(instrument=None, candidates=candidates)
    return ResolveResult(instrument=None, candidates=[])
