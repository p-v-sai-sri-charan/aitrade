"""In-memory, TTL'd store for order previews.

An order can only be confirmed against a preview that was just shown to the
user (`/orders/preview` -> `/orders/confirm`), which is what makes voice
confirmations like "Confirm buy" safe -- there is always exactly one
concrete, already-risk-checked order behind the confirmation.

This is per-process and resets on restart, which is an acceptable MVP
simplification for a single-instance deployment; a multi-worker deployment
would move this into Redis (already configured via REDIS_URL).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from threading import Lock
from typing import Optional

from broker_core.models import OrderRequest
from risk_engine.types import RiskCheckResult

PREVIEW_TTL_SECONDS = 120


@dataclass
class StoredPreview:
    preview_id: str
    order_request: OrderRequest
    company_name: str
    risk_check: RiskCheckResult
    estimated_price: float
    estimated_value: float
    estimated_brokerage: float
    estimated_taxes: float
    estimated_total: float
    created_at: float
    expires_at: float


class PreviewStore:
    def __init__(self) -> None:
        self._store: dict[str, StoredPreview] = {}
        self._lock = Lock()

    def create(
        self,
        order_request: OrderRequest,
        company_name: str,
        risk_check: RiskCheckResult,
        estimated_price: float,
        estimated_value: float,
        estimated_brokerage: float,
        estimated_taxes: float,
        estimated_total: float,
    ) -> StoredPreview:
        now = time.time()
        preview = StoredPreview(
            preview_id=str(uuid.uuid4()),
            order_request=order_request,
            company_name=company_name,
            risk_check=risk_check,
            estimated_price=estimated_price,
            estimated_value=estimated_value,
            estimated_brokerage=estimated_brokerage,
            estimated_taxes=estimated_taxes,
            estimated_total=estimated_total,
            created_at=now,
            expires_at=now + PREVIEW_TTL_SECONDS,
        )
        with self._lock:
            self._prune()
            self._store[preview.preview_id] = preview
        return preview

    def get(self, preview_id: str) -> Optional[StoredPreview]:
        with self._lock:
            self._prune()
            return self._store.get(preview_id)

    def pop(self, preview_id: str) -> Optional[StoredPreview]:
        with self._lock:
            self._prune()
            return self._store.pop(preview_id, None)

    def _prune(self) -> None:
        now = time.time()
        expired = [pid for pid, p in self._store.items() if p.expires_at < now]
        for pid in expired:
            del self._store[pid]


preview_store = PreviewStore()
