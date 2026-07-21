from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import BrokerDep
from app.mappers import quote_to_schema
from app.schemas import QuoteSchema

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/{symbol}", response_model=QuoteSchema)
async def get_quote(symbol: str, broker: BrokerDep) -> QuoteSchema:
    instrument = await broker.instruments.get(symbol)
    if instrument is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{symbol}' is not a recognised NSE instrument.",
        )

    quote = await broker.market_data.get_quote(instrument.symbol, instrument.company_name)
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Market data for '{instrument.symbol}' is temporarily unavailable. Please try again shortly.",
        )
    return quote_to_schema(quote)
