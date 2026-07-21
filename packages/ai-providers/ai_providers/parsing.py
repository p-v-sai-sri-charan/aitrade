"""Shared, defensive JSON->TradeIntent parsing for LLM-backed providers.

An LLM can return malformed JSON, markdown fences, or garbage. This never
raises -- on any problem it degrades to a low-confidence UNKNOWN intent so
the pipeline can surface "I didn't understand that" instead of crashing.
The backend independently re-validates whatever comes out of here.
"""

from __future__ import annotations

import json
import re

from ai_providers.types import CommandLanguage, TradeIntent

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

_VALID_INTENTS = {
    "PLACE_ORDER",
    "CANCEL_ORDER",
    "VIEW_PORTFOLIO",
    "VIEW_ORDERS",
    "VIEW_POSITION",
    "UNKNOWN",
}
_VALID_LANGUAGES = {"hi-IN", "en-IN", "hinglish"}
_VALID_SIDES = {"BUY", "SELL"}
_VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


def _extract_json_object(raw_text: str) -> dict | None:
    stripped = raw_text.strip()
    stripped = re.sub(r"^```(json)?", "", stripped).strip()
    stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = _JSON_BLOCK_RE.search(raw_text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def parse_llm_json_to_intent(
    raw_text: str, fallback_language: CommandLanguage = "en-IN"
) -> TradeIntent:
    data = _extract_json_object(raw_text)
    if data is None or not isinstance(data, dict):
        return TradeIntent(
            intent="UNKNOWN",
            language=fallback_language,
            confidence=0.0,
            missing_fields=[],
            requires_confirmation=False,
        )

    intent_type = data.get("intent")
    if intent_type not in _VALID_INTENTS:
        intent_type = "UNKNOWN"

    language = data.get("language")
    if language not in _VALID_LANGUAGES:
        language = fallback_language

    side = data.get("side")
    if side not in _VALID_SIDES:
        side = None

    order_type = data.get("orderType")
    if order_type not in _VALID_ORDER_TYPES:
        order_type = None

    exchange = data.get("exchange")
    exchange = "NSE" if exchange == "NSE" else None

    product = data.get("product")
    product = "DELIVERY" if product == "DELIVERY" else None

    validity = data.get("validity")
    validity = "DAY" if validity == "DAY" else None

    def _num(value: object) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        return None

    quantity_raw = _num(data.get("quantity"))
    quantity = int(quantity_raw) if quantity_raw is not None else None
    limit_price = _num(data.get("limitPrice"))

    confidence_raw = data.get("confidence")
    confidence = float(confidence_raw) if isinstance(confidence_raw, (int, float)) else 0.5
    confidence = max(0.0, min(1.0, confidence))

    missing_fields = data.get("missingFields")
    if not isinstance(missing_fields, list):
        missing_fields = []
    missing_fields = [str(f) for f in missing_fields]

    ambiguous = data.get("ambiguousSymbolCandidates")
    if not isinstance(ambiguous, list):
        ambiguous = []
    ambiguous = [str(c) for c in ambiguous]

    symbol = data.get("symbol")
    symbol = str(symbol) if isinstance(symbol, str) and symbol.strip() else None

    order_id = data.get("orderId")
    order_id = str(order_id) if isinstance(order_id, str) and order_id.strip() else None

    requires_confirmation = bool(data.get("requiresConfirmation", intent_type in ("PLACE_ORDER", "CANCEL_ORDER")))

    return TradeIntent(
        intent=intent_type,  # type: ignore[arg-type]
        language=language,  # type: ignore[arg-type]
        confidence=confidence,
        missing_fields=missing_fields,
        requires_confirmation=requires_confirmation,
        exchange=exchange,  # type: ignore[arg-type]
        symbol=symbol,
        side=side,  # type: ignore[arg-type]
        quantity=quantity,
        order_type=order_type,  # type: ignore[arg-type]
        limit_price=limit_price,
        product=product,  # type: ignore[arg-type]
        validity=validity,  # type: ignore[arg-type]
        ambiguous_symbol_candidates=ambiguous,
        order_id=order_id,
    )
