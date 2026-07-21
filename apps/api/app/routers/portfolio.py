from __future__ import annotations

from fastapi import APIRouter

from app.deps import BrokerDep
from app.mappers import portfolio_to_schema
from app.schemas import PortfolioSchema

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioSchema)
async def get_portfolio(broker: BrokerDep) -> PortfolioSchema:
    snapshot = await broker.get_portfolio()
    return portfolio_to_schema(snapshot)
