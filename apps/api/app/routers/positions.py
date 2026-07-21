from __future__ import annotations

from fastapi import APIRouter

from app.deps import BrokerDep
from app.mappers import position_to_schema
from app.schemas import PositionSchema

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("", response_model=list[PositionSchema])
async def list_positions(broker: BrokerDep) -> list[PositionSchema]:
    positions = await broker.get_positions()
    return [position_to_schema(p) for p in positions]
