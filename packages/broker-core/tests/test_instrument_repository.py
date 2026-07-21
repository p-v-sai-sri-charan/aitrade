import pytest

from broker_core.instrument_repository import SeededInstrumentRepository, create_instrument_repository
from broker_core.instrument_repository_live import NSEInstrumentRepository, parse_nse_equity_csv


@pytest.mark.asyncio
async def test_seeded_repository_resolves_exact_symbol():
    repo = SeededInstrumentRepository()
    result = await repo.resolve("RELIANCE")
    assert result.is_resolved
    assert result.instrument.symbol == "RELIANCE"


@pytest.mark.asyncio
async def test_seeded_repository_flags_ambiguous_tata():
    repo = SeededInstrumentRepository()
    result = await repo.resolve("tata")
    assert result.is_ambiguous
    assert len(result.candidates) >= 4


@pytest.mark.asyncio
async def test_seeded_repository_search_typeahead():
    repo = SeededInstrumentRepository()
    matches = await repo.search("ta", limit=5)
    assert len(matches) <= 5
    assert all("ta" in m.symbol.lower() or "ta" in m.company_name.lower() for m in matches)


def test_create_instrument_repository_seeded():
    repo = create_instrument_repository("seeded")
    assert isinstance(repo, SeededInstrumentRepository)


def test_create_instrument_repository_nse():
    repo = create_instrument_repository("nse")
    assert isinstance(repo, NSEInstrumentRepository)


def test_create_instrument_repository_unknown_raises():
    with pytest.raises(ValueError):
        create_instrument_repository("not-a-real-source")


SAMPLE_NSE_CSV = (
    "SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE\n"
    "RELIANCE, Reliance Industries Limited,EQ,1995-11-29,10,1,INE002A01018,10\n"
    "TATASTEEL, Tata Steel Limited,EQ,1995-11-29,10,1,INE081A01012,10\n"
    "SOMEBOND, Some Debt Instrument,N1,2020-01-01,1000,1,INE000B00000,1000\n"
)


def test_parse_nse_equity_csv_filters_to_eq_series():
    instruments = parse_nse_equity_csv(SAMPLE_NSE_CSV)
    symbols = {i.symbol for i in instruments}
    assert symbols == {"RELIANCE", "TATASTEEL"}


def test_parse_nse_equity_csv_empty_on_garbage():
    assert parse_nse_equity_csv("not,a,valid,csv\nheader\n") == []


@pytest.mark.asyncio
async def test_nse_repository_falls_back_to_seeded_on_refresh_failure(monkeypatch):
    import httpx

    async def failing_get(self, url, **kwargs):
        raise httpx.ConnectError("simulated network failure", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", failing_get)

    repo = NSEInstrumentRepository(cache_ttl_seconds=0)
    count = await repo.refresh()
    assert count == 20  # still serving the seeded fallback list
    assert repo.last_refreshed_at is None

    result = await repo.resolve("RELIANCE")
    assert result.is_resolved


@pytest.mark.asyncio
async def test_nse_repository_refresh_success_replaces_instruments(monkeypatch):
    import httpx

    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, text=SAMPLE_NSE_CSV, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    repo = NSEInstrumentRepository(cache_ttl_seconds=3600)
    count = await repo.refresh()
    assert count == 2
    assert repo.last_refreshed_at is not None

    all_instruments = await repo.all_instruments()
    assert {i.symbol for i in all_instruments} == {"RELIANCE", "TATASTEEL"}
