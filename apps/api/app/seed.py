"""Seeds demo data on first startup so the UI isn't empty on a fresh
`docker compose up --build`. Safe to call on every startup -- it is a
no-op once any orders exist.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AuditLogModel, OrderModel, PositionModel
from app.repositories import get_or_create_portfolio_state, get_or_create_settings


def seed_demo_data(db: Session, settings: Settings) -> None:
    get_or_create_settings(db, settings)
    state = get_or_create_portfolio_state(db, settings)

    already_seeded = db.execute(select(OrderModel).limit(1)).scalar_one_or_none() is not None
    if already_seeded:
        return

    now = datetime.now(timezone.utc)
    demo_buy_order_id = str(uuid.uuid4())

    demo_position = PositionModel(
        symbol="RELIANCE",
        company_name="Reliance Industries Ltd",
        quantity=10,
        average_price=2900.0,
        realized_pnl=0.0,
    )
    db.add(demo_position)

    demo_orders = [
        OrderModel(
            id=demo_buy_order_id,
            exchange="NSE",
            symbol="RELIANCE",
            company_name="Reliance Industries Ltd",
            side="BUY",
            quantity=10,
            filled_quantity=10,
            order_type="MARKET",
            limit_price=None,
            average_fill_price=2900.0,
            product="DELIVERY",
            validity="DAY",
            status="FILLED",
            brokerage=20.0,
            taxes=3.6,
            rejection_reason=None,
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
        ),
        OrderModel(
            exchange="NSE",
            symbol="TCS",
            company_name="Tata Consultancy Services Ltd",
            side="BUY",
            quantity=5,
            filled_quantity=0,
            order_type="LIMIT",
            limit_price=3700.0,
            average_fill_price=None,
            product="DELIVERY",
            validity="DAY",
            status="PENDING",
            brokerage=0.0,
            taxes=0.0,
            rejection_reason=None,
            created_at=now - timedelta(minutes=30),
            updated_at=now - timedelta(minutes=30),
        ),
        OrderModel(
            exchange="NSE",
            symbol="MARUTI",
            company_name="Maruti Suzuki India Ltd",
            side="BUY",
            quantity=500,
            filled_quantity=0,
            order_type="MARKET",
            limit_price=None,
            average_fill_price=None,
            product="DELIVERY",
            validity="DAY",
            status="REJECTED",
            brokerage=0.0,
            taxes=0.0,
            rejection_reason="Order value exceeds your configured limit.",
            created_at=now - timedelta(hours=5),
            updated_at=now - timedelta(hours=5),
        ),
    ]
    db.add_all(demo_orders)

    demo_audit = AuditLogModel(
        timestamp=now - timedelta(hours=2),
        original_transcript="Reliance ke 10 shares market price par buy karo.",
        detected_language="hinglish",
        parsed_intent={
            "intent": "PLACE_ORDER",
            "symbol": "RELIANCE",
            "side": "BUY",
            "quantity": 10,
            "orderType": "MARKET",
            "language": "hinglish",
            "confidence": 0.92,
            "missingFields": [],
            "requiresConfirmation": True,
        },
        ai_provider="mock",
        validation_valid=True,
        validation_errors=[],
        risk_check={"allowed": True, "code": "OK", "message": "All risk checks passed.", "requiresOverride": False},
        user_confirmed=True,
        order_response_summary="FILLED: BUY 10 RELIANCE",
        order_id=demo_buy_order_id,
    )
    db.add(demo_audit)

    state.available_balance = settings.paper_starting_balance - (10 * 2900.0 + 20.0 + 3.6)
    db.commit()
