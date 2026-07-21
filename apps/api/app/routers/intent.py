from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from ai_providers import TradeIntentInput
from app.audit import write_audit_log
from app.deps import AIProviderDep, DbSession, InstrumentRepositoryDep
from app.instrument_resolver import resolve_symbol
from app.schemas import IntentParseResponse, TradeIntentInputSchema, TradeIntentSchema
from app.security import sanitize_text

router = APIRouter(prefix="/intent", tags=["intent"])


@router.post("/parse", response_model=IntentParseResponse)
async def parse_intent(
    payload: TradeIntentInputSchema,
    db: DbSession,
    ai_provider: AIProviderDep,
    instruments: InstrumentRepositoryDep,
) -> IntentParseResponse:
    transcript = sanitize_text(payload.transcript)

    result = await ai_provider.extract_trade_intent(
        TradeIntentInput(
            transcript=transcript,
            detected_language=payload.detected_language,
            conversation_context=payload.conversation_context,
        )
    )

    # Independent backend schema validation -- the AI's dataclass is never
    # trusted as-is, even though it came from our own provider abstraction.
    intent_schema = TradeIntentSchema.model_validate(asdict(result.intent))

    if intent_schema.intent == "PLACE_ORDER" and intent_schema.symbol:
        resolved = await resolve_symbol(intent_schema.symbol, instruments)
        if resolved.ambiguous_candidates:
            intent_schema.ambiguous_symbol_candidates = [
                f"{c.symbol} - {c.company_name}" for c in resolved.ambiguous_candidates
            ]
            if "symbol" not in intent_schema.missing_fields:
                intent_schema.missing_fields = [*intent_schema.missing_fields, "symbol"]
        elif resolved.instrument:
            intent_schema.symbol = resolved.instrument.symbol
        else:
            if "symbol" not in intent_schema.missing_fields:
                intent_schema.missing_fields = [*intent_schema.missing_fields, "symbol"]

    validation_valid = not intent_schema.missing_fields and not intent_schema.ambiguous_symbol_candidates

    write_audit_log(
        db,
        original_transcript=transcript,
        detected_language=intent_schema.language,
        parsed_intent=intent_schema.model_dump(mode="json", by_alias=True),
        ai_provider=result.provider,
        validation_valid=validation_valid,
        validation_errors=intent_schema.missing_fields,
    )

    return IntentParseResponse(intent=intent_schema, provider=result.provider)
