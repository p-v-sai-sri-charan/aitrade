from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import InstrumentRepositoryDep
from app.schemas import InstrumentSchema, InstrumentStatusSchema
from app.security import rate_limit_order_actions

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("/search", response_model=list[InstrumentSchema])
async def search_instruments(
    instruments: InstrumentRepositoryDep,
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=20, le=50),
) -> list[InstrumentSchema]:
    matches = await instruments.search(q, limit)
    return [
        InstrumentSchema(symbol=i.symbol, companyName=i.company_name, exchange="NSE") for i in matches
    ]


@router.get("/status", response_model=InstrumentStatusSchema)
async def instrument_status(instruments: InstrumentRepositoryDep) -> InstrumentStatusSchema:
    all_instruments = await instruments.all_instruments()
    return InstrumentStatusSchema(
        source=instruments.source,
        instrumentCount=len(all_instruments),
        lastRefreshedAt=instruments.last_refreshed_at,
    )


@router.post(
    "/refresh",
    response_model=InstrumentStatusSchema,
    dependencies=[Depends(rate_limit_order_actions)],
)
async def refresh_instruments(instruments: InstrumentRepositoryDep) -> InstrumentStatusSchema:
    """Forces an immediate refresh of the instrument universe. A no-op that
    just reports the current (seeded) count when INSTRUMENT_SOURCE=seeded.
    """
    count = await instruments.refresh()
    return InstrumentStatusSchema(
        source=instruments.source,
        instrumentCount=count,
        lastRefreshedAt=instruments.last_refreshed_at,
    )
