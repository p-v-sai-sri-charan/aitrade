from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.deps import BrokerDep
from app.mappers import quote_to_schema
from app.schemas import QuoteSchema

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/{symbol}", response_model=QuoteSchema)
async def get_quote(symbol: str, broker: BrokerDep) -> QuoteSchema:
    quote = await broker.get_quote(symbol)
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{symbol}' is not a recognised NSE instrument.",
        )
    return quote_to_schema(quote)
