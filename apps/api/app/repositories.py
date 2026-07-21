"""SQLAlchemy-backed implementation of `broker_core.store.BrokerStore`, plus
small repositories for settings and duplicate-order lookups. This is the
seam between the DB-agnostic `PaperBroker` and Postgres.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import OrderModel, PortfolioStateModel, PositionModel, SettingsModel
from broker_core.models import OrderRecord, PositionRecord


def _today_iso() -> str:
    return date.today().isoformat()


def get_or_create_portfolio_state(db: Session, settings: Settings) -> PortfolioStateModel:
    state = db.get(PortfolioStateModel, 1)
    if state is None:
        state = PortfolioStateModel(
            id=1,
            available_balance=settings.paper_starting_balance,
            realized_pnl_today=0.0,
            pnl_reset_date=_today_iso(),
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    elif state.pnl_reset_date != _today_iso():
        state.realized_pnl_today = 0.0
        state.pnl_reset_date = _today_iso()
        db.commit()
        db.refresh(state)
    return state


def get_or_create_settings(db: Session, defaults: Settings) -> SettingsModel:
    row = db.get(SettingsModel, 1)
    if row is None:
        row = SettingsModel(
            id=1,
            ai_provider=defaults.ai_provider,
            language_preference="auto",
            voice_output_enabled=True,
            risk_max_order_value=defaults.risk_max_order_value,
            risk_max_quantity=defaults.risk_max_quantity,
            risk_max_price_deviation_pct=defaults.risk_max_price_deviation_pct,
            risk_daily_loss_limit=defaults.risk_daily_loss_limit,
            trading_kill_switch=defaults.trading_kill_switch,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


class SQLAlchemyBrokerStore:
    """Implements the `BrokerStore` protocol on top of a SQLAlchemy session."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    # --- balance / realized pnl ---

    def get_balance(self) -> float:
        return get_or_create_portfolio_state(self.db, self.settings).available_balance

    def set_balance(self, value: float) -> None:
        state = get_or_create_portfolio_state(self.db, self.settings)
        state.available_balance = value
        self.db.commit()

    def get_realized_pnl_today(self) -> float:
        return get_or_create_portfolio_state(self.db, self.settings).realized_pnl_today

    def add_realized_pnl_today(self, delta: float) -> None:
        state = get_or_create_portfolio_state(self.db, self.settings)
        state.realized_pnl_today += delta
        self.db.commit()

    # --- positions ---

    def list_positions(self) -> list[PositionRecord]:
        rows = self.db.execute(select(PositionModel)).scalars().all()
        return [
            PositionRecord(
                symbol=r.symbol,
                company_name=r.company_name,
                quantity=r.quantity,
                average_price=r.average_price,
                realized_pnl=r.realized_pnl,
            )
            for r in rows
        ]

    def get_position(self, symbol: str) -> PositionRecord | None:
        row = self.db.get(PositionModel, symbol)
        if row is None:
            return None
        return PositionRecord(
            symbol=row.symbol,
            company_name=row.company_name,
            quantity=row.quantity,
            average_price=row.average_price,
            realized_pnl=row.realized_pnl,
        )

    def upsert_position(self, position: PositionRecord) -> None:
        row = self.db.get(PositionModel, position.symbol)
        if row is None:
            row = PositionModel(symbol=position.symbol)
            self.db.add(row)
        row.company_name = position.company_name
        row.quantity = position.quantity
        row.average_price = position.average_price
        row.realized_pnl = position.realized_pnl
        self.db.commit()

    def remove_position(self, symbol: str) -> None:
        row = self.db.get(PositionModel, symbol)
        if row is not None:
            self.db.delete(row)
            self.db.commit()

    # --- orders ---

    def add_order(self, order: OrderRecord) -> None:
        row = OrderModel(
            id=order.id,
            exchange=order.exchange,
            symbol=order.symbol,
            company_name=order.company_name,
            side=order.side,
            quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            order_type=order.order_type,
            limit_price=order.limit_price,
            average_fill_price=order.average_fill_price,
            product=order.product,
            validity=order.validity,
            status=order.status,
            brokerage=order.brokerage,
            taxes=order.taxes,
            rejection_reason=order.rejection_reason,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        self.db.add(row)
        self.db.commit()

    def update_order(self, order: OrderRecord) -> None:
        row = self.db.get(OrderModel, order.id)
        if row is None:
            self.add_order(order)
            return
        row.status = order.status
        row.filled_quantity = order.filled_quantity
        row.average_fill_price = order.average_fill_price
        row.brokerage = order.brokerage
        row.taxes = order.taxes
        row.rejection_reason = order.rejection_reason
        row.updated_at = order.updated_at
        self.db.commit()

    def get_order(self, order_id: str) -> OrderRecord | None:
        row = self.db.get(OrderModel, order_id)
        if row is None:
            return None
        return _order_model_to_record(row)

    def list_orders(self) -> list[OrderRecord]:
        rows = (
            self.db.execute(select(OrderModel).order_by(OrderModel.created_at.desc()))
            .scalars()
            .all()
        )
        return [_order_model_to_record(r) for r in rows]

    def list_recent_orders(self, since: datetime) -> list[OrderRecord]:
        rows = (
            self.db.execute(select(OrderModel).where(OrderModel.created_at >= since))
            .scalars()
            .all()
        )
        return [_order_model_to_record(r) for r in rows]


def _order_model_to_record(row: OrderModel) -> OrderRecord:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    updated_at = row.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return OrderRecord(
        id=row.id,
        exchange=row.exchange,
        symbol=row.symbol,
        company_name=row.company_name,
        side=row.side,
        quantity=row.quantity,
        filled_quantity=row.filled_quantity,
        order_type=row.order_type,
        limit_price=row.limit_price,
        average_fill_price=row.average_fill_price,
        product=row.product,
        validity=row.validity,
        status=row.status,
        brokerage=row.brokerage,
        taxes=row.taxes,
        rejection_reason=row.rejection_reason,
        created_at=created_at,
        updated_at=updated_at,
    )
