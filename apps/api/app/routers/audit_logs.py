from __future__ import annotations

from sqlalchemy import select

from fastapi import APIRouter, Query

from app.deps import DbSession
from app.models import AuditLogModel
from app.schemas import AuditLogEntrySchema

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=list[AuditLogEntrySchema])
async def list_audit_logs(
    db: DbSession,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AuditLogEntrySchema]:
    rows = (
        db.execute(
            select(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).limit(limit).offset(offset)
        )
        .scalars()
        .all()
    )
    return [
        AuditLogEntrySchema(
            id=r.id,
            timestamp=r.timestamp,
            originalTranscript=r.original_transcript,
            detectedLanguage=r.detected_language,
            parsedIntent=r.parsed_intent,
            aiProvider=r.ai_provider,
            validationValid=r.validation_valid,
            validationErrors=r.validation_errors or [],
            riskCheck=r.risk_check,
            userConfirmed=r.user_confirmed,
            orderResponseSummary=r.order_response_summary,
            orderId=r.order_id,
        )
        for r in rows
    ]
