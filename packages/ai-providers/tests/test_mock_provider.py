import pytest

from ai_providers.mock_provider import MockProvider
from ai_providers.types import TradeIntentInput


@pytest.fixture
def provider() -> MockProvider:
    return MockProvider()


@pytest.mark.asyncio
async def test_hinglish_limit_buy_order(provider: MockProvider):
    result = await provider.extract_trade_intent(
        TradeIntentInput(transcript="Reliance ke 10 shares 2950 limit price par buy karo.")
    )
    intent = result.intent
    assert intent.intent == "PLACE_ORDER"
    assert intent.symbol == "Reliance"
    assert intent.side == "BUY"
    assert intent.quantity == 10
    assert intent.order_type == "LIMIT"
    assert intent.limit_price == 2950
    assert intent.language == "hinglish"
    assert intent.missing_fields == []
    assert intent.requires_confirmation is True


@pytest.mark.asyncio
async def test_english_market_sell_order(provider: MockProvider):
    result = await provider.extract_trade_intent(
        TradeIntentInput(transcript="Sell 5 shares of Infosys at market price")
    )
    intent = result.intent
    assert intent.intent == "PLACE_ORDER"
    assert intent.side == "SELL"
    assert intent.quantity == 5
    assert intent.symbol == "Infosys"
    assert intent.order_type == "MARKET"


@pytest.mark.asyncio
async def test_ambiguous_company_name_not_guessed(provider: MockProvider):
    result = await provider.extract_trade_intent(
        TradeIntentInput(transcript="Tata ka share buy karo.")
    )
    intent = result.intent
    assert intent.intent == "PLACE_ORDER"
    assert intent.symbol == "Tata"
    # The mock provider never resolves symbols itself -- the backend's
    # instrument resolver is responsible for detecting the ambiguity.
    assert "quantity" in intent.missing_fields


@pytest.mark.asyncio
async def test_view_portfolio_intent():
    provider = MockProvider()
    result = await provider.extract_trade_intent(
        TradeIntentInput(transcript="mera portfolio dikhao")
    )
    assert result.intent.intent == "VIEW_PORTFOLIO"
    assert result.intent.requires_confirmation is False


@pytest.mark.asyncio
async def test_view_orders_intent():
    provider = MockProvider()
    result = await provider.extract_trade_intent(TradeIntentInput(transcript="show my orders"))
    assert result.intent.intent == "VIEW_ORDERS"


@pytest.mark.asyncio
async def test_unknown_intent_for_gibberish():
    provider = MockProvider()
    result = await provider.extract_trade_intent(TradeIntentInput(transcript="asdkj qweoiu"))
    assert result.intent.intent == "UNKNOWN"
    assert result.intent.confidence < 0.5


@pytest.mark.asyncio
async def test_missing_quantity_flagged(provider: MockProvider):
    result = await provider.extract_trade_intent(
        TradeIntentInput(transcript="Buy Reliance limit 2950")
    )
    intent = result.intent
    assert "quantity" in intent.missing_fields


@pytest.mark.asyncio
async def test_explain_risk_returns_text(provider: MockProvider):
    from ai_providers.types import RiskExplanationInput

    text = await provider.explain_risk(
        RiskExplanationInput(
            risk_code="ORDER_VALUE_LIMIT_EXCEEDED",
            message="Order value exceeds your configured limit.",
            language="en-IN",
        )
    )
    assert "limit" in text.lower()
