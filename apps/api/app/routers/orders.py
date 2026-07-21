from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.audit import write_audit_log
from app.deps import AppSettings, BrokerDep, DbSession, RiskLimitsDep
from app.mappers import order_to_schema
from app.models import IdempotencyKeyModel
from app.schemas import (
    OrderConfirmRequestSchema,
    OrderPreviewSchema,
    OrderRequestSchema,
    OrderSchema,
    RiskCheckResultSchema,
)
from app.security import rate_limit_order_actions
from app.services.preview_store import preview_store
from app.services.risk_orchestration import evaluate_order
from app.ws_manager import order_updates_manager
from broker_core.paper_broker import OrderNotCancellableError, OrderNotFoundError, PaperBrokerConfig
from app.repositories import get_or_create_settings

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(rate_limit_order_actions)])


@router.post("/preview", response_model=OrderPreviewSchema)
async def preview_order(
    payload: OrderRequestSchema,
    db: DbSession,
    settings: AppSettings,
    broker: BrokerDep,
    limits: RiskLimitsDep,
) -> OrderPreviewSchema:
    settings_row = get_or_create_settings(db, settings)
    paper_config = PaperBrokerConfig(
        slippage_bps=settings.paper_slippage_bps,
        brokerage_flat=settings.paper_brokerage_flat,
        stt_rate_sell=settings.paper_stt_rate_sell,
        gst_rate=settings.paper_gst_rate,
    )

    evaluation = await evaluate_order(
        payload,
        broker=broker,
        limits=limits,
        trading_kill_switch_active=settings_row.trading_kill_switch,
        paper_config=paper_config,
    )

    stored = preview_store.create(
        order_request=evaluation.order_request,
        company_name=evaluation.company_name,
        risk_check=evaluation.risk_check,
        estimated_price=evaluation.estimated_price,
        estimated_value=evaluation.estimated_value,
        estimated_brokerage=evaluation.estimated_brokerage,
        estimated_taxes=evaluation.estimated_taxes,
        estimated_total=evaluation.estimated_total,
    )

    return OrderPreviewSchema(
        previewId=stored.preview_id,
        request=payload,
        companyName=evaluation.company_name,
        estimatedPrice=evaluation.estimated_price,
        estimatedValue=evaluation.estimated_value,
        estimatedBrokerage=evaluation.estimated_brokerage,
        estimatedTaxes=evaluation.estimated_taxes,
        estimatedTotal=evaluation.estimated_total,
        riskCheck=RiskCheckResultSchema(**evaluation.risk_check.to_dict()),
        expiresAt=datetime.fromtimestamp(stored.expires_at, tz=timezone.utc),
    )


@router.post("/confirm", response_model=OrderSchema)
async def confirm_order(
    payload: OrderConfirmRequestSchema,
    db: DbSession,
    settings: AppSettings,
    broker: BrokerDep,
    limits: RiskLimitsDep,
) -> OrderSchema:
    existing_key = db.get(IdempotencyKeyModel, payload.idempotency_key)
    if existing_key is not None and existing_key.response_json is not None:
        return OrderSchema.model_validate(existing_key.response_json)

    stored = preview_store.get(payload.preview_id)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This order preview has expired or was not found. Please request a new preview.",
        )

    settings_row = get_or_create_settings(db, settings)
    paper_config = PaperBrokerConfig(
        slippage_bps=settings.paper_slippage_bps,
        brokerage_flat=settings.paper_brokerage_flat,
        stt_rate_sell=settings.paper_stt_rate_sell,
        gst_rate=settings.paper_gst_rate,
    )

    # Re-validate against CURRENT state -- never trust the numbers shown in
    # an earlier preview when actually executing.
    order_request_schema = OrderRequestSchema(
        exchange=stored.order_request.exchange,  # type: ignore[arg-type]
        symbol=stored.order_request.symbol,
        side=stored.order_request.side,  # type: ignore[arg-type]
        quantity=stored.order_request.quantity,
        orderType=stored.order_request.order_type,  # type: ignore[arg-type]
        limitPrice=stored.order_request.limit_price,
        product=stored.order_request.product,  # type: ignore[arg-type]
        validity=stored.order_request.validity,  # type: ignore[arg-type]
    )
    evaluation = await evaluate_order(
        order_request_schema,
        broker=broker,
        limits=limits,
        trading_kill_switch_active=settings_row.trading_kill_switch,
        paper_config=paper_config,
    )

    if not evaluation.risk_check.allowed:
        preview_store.pop(payload.preview_id)
        write_audit_log(
            db,
            parsed_intent=None,
            risk_check=evaluation.risk_check.to_dict(),
            user_confirmed=True,
            validation_valid=False,
            order_response_summary=f"REJECTED: {evaluation.risk_check.message}",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"riskCheck": evaluation.risk_check.to_dict()},
        )

    record = await broker.place_order(evaluation.order_request)
    preview_store.pop(payload.preview_id)

    order_schema = order_to_schema(record)

    idempotency_row = IdempotencyKeyModel(
        key=payload.idempotency_key,
        order_id=record.id,
        response_json=order_schema.model_dump(mode="json", by_alias=True),
    )
    db.merge(idempotency_row)
    db.commit()

    write_audit_log(
        db,
        risk_check=evaluation.risk_check.to_dict(),
        user_confirmed=True,
        validation_valid=True,
        order_response_summary=f"{record.status}: {record.side} {record.quantity} {record.symbol}",
        order_id=record.id,
    )

    await order_updates_manager.broadcast(
        {"type": "ORDER_UPDATE", "order": order_schema.model_dump(mode="json", by_alias=True)}
    )

    return order_schema


@router.post("/{order_id}/cancel", response_model=OrderSchema)
async def cancel_order(order_id: str, db: DbSession, broker: BrokerDep) -> OrderSchema:
    try:
        record = await broker.cancel_order(order_id)
    except OrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    except OrderNotCancellableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    order_schema = order_to_schema(record)

    write_audit_log(
        db,
        user_confirmed=True,
        validation_valid=True,
        order_response_summary=f"CANCELLED: {record.symbol}",
        order_id=record.id,
    )

    await order_updates_manager.broadcast(
        {"type": "ORDER_UPDATE", "order": order_schema.model_dump(mode="json", by_alias=True)}
    )

    return order_schema


@router.get("", response_model=list[OrderSchema])
async def list_orders(broker: BrokerDep, status_filter: str | None = None) -> list[OrderSchema]:
    orders = await broker.get_orders()
    if status_filter:
        orders = [o for o in orders if o.status == status_filter.upper()]
    return [order_to_schema(o) for o in orders]
