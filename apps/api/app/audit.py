"""Structured audit logging. Every parse / validate / confirm / order-response
cycle is recorded here. NEVER pass API keys or other secrets into this module.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditLogModel


def write_audit_log(
    db: Session,
    *,
    original_transcript: Optional[str] = None,
    detected_language: Optional[str] = None,
    parsed_intent: Optional[dict[str, Any]] = None,
    ai_provider: Optional[str] = None,
    validation_valid: bool = True,
    validation_errors: Optional[list[str]] = None,
    risk_check: Optional[dict[str, Any]] = None,
    user_confirmed: Optional[bool] = None,
    order_response_summary: Optional[str] = None,
    order_id: Optional[str] = None,
) -> AuditLogModel:
    entry = AuditLogModel(
        original_transcript=original_transcript,
        detected_language=detected_language,
        parsed_intent=parsed_intent,
        ai_provider=ai_provider,
        validation_valid=validation_valid,
        validation_errors=validation_errors or [],
        risk_check=risk_check,
        user_confirmed=user_confirmed,
        order_response_summary=order_response_summary,
        order_id=order_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
