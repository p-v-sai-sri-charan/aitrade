from broker_core.instruments import resolve_instrument


def test_exact_symbol_resolves():
    result = resolve_instrument("RELIANCE")
    assert result.is_resolved
    assert result.instrument.symbol == "RELIANCE"


def test_alias_resolves_uniquely():
    result = resolve_instrument("infosys")
    assert result.is_resolved
    assert result.instrument.symbol == "INFY"


def test_ambiguous_tata_returns_multiple_candidates():
    result = resolve_instrument("tata")
    assert result.is_ambiguous
    symbols = {c.symbol for c in result.candidates}
    assert "TATAMOTORS" in symbols
    assert "TATASTEEL" in symbols
    assert len(result.candidates) >= 4


def test_unknown_symbol_not_found():
    result = resolve_instrument("NOTAREALCOMPANY")
    assert result.is_not_found
