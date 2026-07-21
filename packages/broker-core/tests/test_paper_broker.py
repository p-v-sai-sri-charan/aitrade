import pytest

from broker_core.market_data import SEED_PRICES
from broker_core.models import OrderRequest
from broker_core.paper_broker import PaperBroker, PaperBrokerConfig
from broker_core.store import InMemoryBrokerStore


@pytest.fixture
def broker() -> PaperBroker:
    store = InMemoryBrokerStore(starting_balance=1_000_000)
    return PaperBroker(store, PaperBrokerConfig(slippage_bps=0, brokerage_flat=20, gst_rate=0.18))


@pytest.mark.asyncio
async def test_market_buy_fills_immediately(broker: PaperBroker):
    order = OrderRequest(
        exchange="NSE",
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        side="BUY",
        quantity=10,
        order_type="MARKET",
        limit_price=None,
        product="DELIVERY",
        validity="DAY",
    )
    record = await broker.place_order(order)
    assert record.status == "FILLED"
    assert record.filled_quantity == 10
    assert record.average_fill_price is not None

    positions = await broker.get_positions()
    assert len(positions) == 1
    assert positions[0].symbol == "RELIANCE"
    assert positions[0].quantity == 10


@pytest.mark.asyncio
async def test_limit_buy_below_market_stays_pending(broker: PaperBroker):
    low_price = SEED_PRICES["RELIANCE"] * 0.5
    order = OrderRequest(
        exchange="NSE",
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        side="BUY",
        quantity=10,
        order_type="LIMIT",
        limit_price=low_price,
        product="DELIVERY",
        validity="DAY",
    )
    record = await broker.place_order(order)
    assert record.status == "PENDING"


@pytest.mark.asyncio
async def test_sell_without_holdings_rejected(broker: PaperBroker):
    order = OrderRequest(
        exchange="NSE",
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        side="SELL",
        quantity=10,
        order_type="MARKET",
        limit_price=None,
        product="DELIVERY",
        validity="DAY",
    )
    record = await broker.place_order(order)
    assert record.status == "REJECTED"
    assert record.rejection_reason is not None


@pytest.mark.asyncio
async def test_buy_then_sell_realizes_pnl(broker: PaperBroker):
    buy = OrderRequest(
        exchange="NSE",
        symbol="TCS",
        company_name="Tata Consultancy Services Ltd",
        side="BUY",
        quantity=5,
        order_type="MARKET",
        limit_price=None,
        product="DELIVERY",
        validity="DAY",
    )
    await broker.place_order(buy)

    sell = OrderRequest(
        exchange="NSE",
        symbol="TCS",
        company_name="Tata Consultancy Services Ltd",
        side="SELL",
        quantity=5,
        order_type="MARKET",
        limit_price=None,
        product="DELIVERY",
        validity="DAY",
    )
    sell_record = await broker.place_order(sell)
    assert sell_record.status == "FILLED"

    positions = await broker.get_positions()
    assert len(positions) == 0

    portfolio = await broker.get_portfolio()
    assert portfolio.available_balance > 0


@pytest.mark.asyncio
async def test_cancel_pending_order(broker: PaperBroker):
    low_price = SEED_PRICES["RELIANCE"] * 0.5
    order = OrderRequest(
        exchange="NSE",
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        side="BUY",
        quantity=10,
        order_type="LIMIT",
        limit_price=low_price,
        product="DELIVERY",
        validity="DAY",
    )
    record = await broker.place_order(order)
    cancelled = await broker.cancel_order(record.id)
    assert cancelled.status == "CANCELLED"


@pytest.mark.asyncio
async def test_insufficient_balance_rejected(broker: PaperBroker):
    order = OrderRequest(
        exchange="NSE",
        symbol="MARUTI",
        company_name="Maruti Suzuki India Ltd",
        side="BUY",
        quantity=1000,
        order_type="MARKET",
        limit_price=None,
        product="DELIVERY",
        validity="DAY",
    )
    record = await broker.place_order(order)
    assert record.status == "REJECTED"
