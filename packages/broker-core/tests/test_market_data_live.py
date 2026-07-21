import httpx
import pytest

from broker_core.market_data import SeededMarketDataProvider
from broker_core.market_data_live import YahooFinanceMarketDataProvider
from broker_core.market_data_provider import create_market_data_provider

SAMPLE_YAHOO_RESPONSE = {
    "chart": {
        "result": [
            {
                "meta": {
                    "regularMarketPrice": 2960.5,
                    "previousClose": 2950.0,
                    "longName": "Reliance Industries Limited",
                }
            }
        ]
    }
}


@pytest.mark.asyncio
async def test_yahoo_provider_parses_successful_response(monkeypatch):
    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, json=SAMPLE_YAHOO_RESPONSE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = YahooFinanceMarketDataProvider(cache_ttl_seconds=0)
    quote = await provider.get_quote("RELIANCE")
    assert quote is not None
    assert quote.symbol == "RELIANCE"
    assert quote.company_name == "Reliance Industries Limited"
    assert quote.last_price == 2960.5
    assert quote.previous_close == 2950.0
    assert quote.change_pct == pytest.approx(0.36, abs=0.01)


@pytest.mark.asyncio
async def test_yahoo_provider_prefers_passed_company_name(monkeypatch):
    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, json=SAMPLE_YAHOO_RESPONSE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = YahooFinanceMarketDataProvider(cache_ttl_seconds=0)
    quote = await provider.get_quote("RELIANCE", "Reliance Industries Ltd")
    assert quote.company_name == "Reliance Industries Ltd"


@pytest.mark.asyncio
async def test_yahoo_provider_returns_none_on_network_failure(monkeypatch):
    async def failing_get(self, url, **kwargs):
        raise httpx.ConnectError("simulated network failure", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", failing_get)

    provider = YahooFinanceMarketDataProvider(cache_ttl_seconds=0)
    quote = await provider.get_quote("RELIANCE")
    assert quote is None


@pytest.mark.asyncio
async def test_yahoo_provider_returns_none_on_empty_chart_result(monkeypatch):
    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, json={"chart": {"result": []}}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = YahooFinanceMarketDataProvider(cache_ttl_seconds=0)
    quote = await provider.get_quote("NOTAREALSTOCK")
    assert quote is None


@pytest.mark.asyncio
async def test_yahoo_provider_caches_within_ttl(monkeypatch):
    call_count = 0

    async def fake_get(self, url, **kwargs):
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json=SAMPLE_YAHOO_RESPONSE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = YahooFinanceMarketDataProvider(cache_ttl_seconds=60)
    await provider.get_quote("RELIANCE")
    await provider.get_quote("RELIANCE")
    assert call_count == 1


def test_create_market_data_provider_mock_is_default():
    provider = create_market_data_provider()
    assert isinstance(provider, SeededMarketDataProvider)


def test_create_market_data_provider_yahoo():
    provider = create_market_data_provider("yahoo")
    assert isinstance(provider, YahooFinanceMarketDataProvider)


def test_create_market_data_provider_unknown_raises():
    with pytest.raises(ValueError):
        create_market_data_provider("not-a-real-provider")
