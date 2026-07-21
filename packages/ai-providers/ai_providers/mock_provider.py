"""Deterministic, rule-based provider.

This is the DEFAULT provider (`AI_PROVIDER=mock`) so the whole project runs
end-to-end with zero API keys. It is a plain regex/heuristic parser for
Hindi, Hinglish, and English trade commands -- not a language model. Real
providers (Anthropic/OpenAI/Gemini/local/Ollama) will generally be far more
robust; this exists so contributors and CI never need a paid API key.
"""

from __future__ import annotations

import re

from ai_providers.types import (
    CommandLanguage,
    RiskExplanationInput,
    TradeIntent,
    TradeIntentInput,
    TradeIntentResult,
)

BUY_WORDS = {"buy", "kharido", "kharid", "kharidna", "kharido please", "kharidiye"}
SELL_WORDS = {"sell", "becho", "bech", "bechna", "bechiye"}
LIMIT_WORDS = {"limit"}
PORTFOLIO_WORDS = {"portfolio", "holdings", "balance"}
ORDERS_WORDS = {"orders", "order list"}
POSITION_WORDS = {"position", "positions"}
CANCEL_WORDS = {"cancel", "radd", "cancel karo", "hatao"}

QUANTITY_KEYWORDS = {"shares", "share", "stock", "stocks", "qty", "quantity", "shabd"}
PRICE_KEYWORDS = {"limit", "price", "rupee", "rupees", "rs", "₹", "@", "rate"}

STOPWORDS = {
    "ke",
    "ka",
    "ki",
    "ko",
    "hai",
    "haan",
    "kar",
    "karo",
    "kro",
    "kardo",
    "kar do",
    "please",
    "the",
    "a",
    "an",
    "shares",
    "share",
    "stock",
    "stocks",
    "of",
    "buy",
    "sell",
    "kharido",
    "kharid",
    "kharidna",
    "kharidiye",
    "becho",
    "bech",
    "bechna",
    "bechiye",
    "limit",
    "price",
    "par",
    "pe",
    "at",
    "market",
    "qty",
    "quantity",
    "order",
    "rupay",
    "rupaye",
    "rupees",
    "rupee",
    "rs",
    "for",
    "and",
    "on",
    "to",
    "my",
    "mera",
    "dikhao",
    "dikhaiye",
    "batao",
    "show",
    "me",
    "portfolio",
    "holdings",
    "balance",
    "orders",
    "positions",
    "position",
    "cancel",
    "radd",
    "hatao",
}

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
HINGLISH_HINTS = {
    "karo",
    "kar",
    "hai",
    "ke",
    "ka",
    "ki",
    "kharido",
    "becho",
    "dikhao",
    "mera",
    "haan",
    "kro",
    "kardo",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w₹.]+", text)


def _detect_language(text: str) -> CommandLanguage:
    if DEVANAGARI_RE.search(text):
        return "hi-IN"
    lowered = text.lower()
    tokens = set(_tokenize(lowered))
    if tokens & HINGLISH_HINTS:
        return "hinglish"
    return "en-IN"


def _detect_side(lowered: str) -> str | None:
    tokens = set(lowered.split())
    if tokens & BUY_WORDS or "buy" in lowered or "kharid" in lowered:
        return "BUY"
    if tokens & SELL_WORDS or "sell" in lowered or "bech" in lowered:
        return "SELL"
    return None


def _extract_numbers(tokens: list[str]) -> list[tuple[float, int]]:
    numbers = []
    for idx, tok in enumerate(tokens):
        cleaned = tok.rstrip(".")
        if re.fullmatch(r"\d+(\.\d+)?", cleaned):
            numbers.append((float(cleaned), idx))
    return numbers


def _extract_quantity_and_price(
    tokens: list[str], order_type: str
) -> tuple[int | None, float | None]:
    lowered_tokens = [t.lower() for t in tokens]
    numbers = _extract_numbers(tokens)
    if not numbers:
        return None, None

    quantity: float | None = None
    price: float | None = None

    def neighbors(idx: int) -> set[str]:
        window = lowered_tokens[max(0, idx - 2) : idx + 3]
        return set(window)

    for value, idx in numbers:
        nearby = neighbors(idx)
        if nearby & QUANTITY_KEYWORDS and quantity is None:
            quantity = value
        elif nearby & PRICE_KEYWORDS and price is None:
            price = value

    remaining = [n for n in numbers if n[0] not in (quantity, price)]
    if quantity is None and remaining:
        quantity = remaining.pop(0)[0]
    if order_type == "LIMIT" and price is None and remaining:
        price = remaining.pop(0)[0]

    qty_int = int(quantity) if quantity is not None else None
    return qty_int, price


def _extract_symbol_text(tokens: list[str]) -> str | None:
    runs: list[list[str]] = []
    current: list[str] = []
    for tok in tokens:
        lowered = tok.lower()
        is_number = bool(re.fullmatch(r"\d+(\.\d+)?", tok))
        if is_number or lowered in STOPWORDS or not re.fullmatch(r"[A-Za-z]+", tok):
            if current:
                runs.append(current)
                current = []
            continue
        current.append(tok)
    if current:
        runs.append(current)

    if not runs:
        return None

    best = max(runs, key=lambda r: sum(len(w) for w in r))
    return " ".join(w.capitalize() for w in best)


class MockProvider:
    """Deterministic rule-based fallback AIProvider. No network calls."""

    name = "mock"

    async def extract_trade_intent(self, input: TradeIntentInput) -> TradeIntentResult:
        transcript = input.transcript.strip()
        lowered = transcript.lower()
        tokens = _tokenize(transcript)
        language = input.detected_language or _detect_language(transcript)

        intent_type = "UNKNOWN"
        if any(w in lowered for w in CANCEL_WORDS) and "order" in lowered:
            intent_type = "CANCEL_ORDER"
        elif any(w in lowered for w in PORTFOLIO_WORDS):
            intent_type = "VIEW_PORTFOLIO"
        elif any(w in lowered for w in POSITION_WORDS):
            intent_type = "VIEW_POSITION"
        elif any(w in lowered for w in ORDERS_WORDS):
            intent_type = "VIEW_ORDERS"
        else:
            side = _detect_side(lowered)
            if side is not None:
                intent_type = "PLACE_ORDER"

        if intent_type != "PLACE_ORDER":
            missing: list[str] = []
            confidence = 0.85 if intent_type != "UNKNOWN" else 0.2
            intent = TradeIntent(
                intent=intent_type,  # type: ignore[arg-type]
                language=language,
                confidence=confidence,
                missing_fields=missing,
                requires_confirmation=intent_type == "CANCEL_ORDER",
            )
            return TradeIntentResult(intent=intent, provider=self.name, raw_provider_output=transcript)

        side = _detect_side(lowered)
        order_type = "LIMIT" if any(w in lowered for w in LIMIT_WORDS) else "MARKET"
        quantity, price = _extract_quantity_and_price(tokens, order_type)
        symbol_text = _extract_symbol_text(tokens)

        missing_fields: list[str] = []
        if not symbol_text:
            missing_fields.append("symbol")
        if side is None:
            missing_fields.append("side")
        if quantity is None:
            missing_fields.append("quantity")
        if order_type == "LIMIT" and price is None:
            missing_fields.append("limitPrice")

        confidence = 0.9 if not missing_fields else max(0.3, 0.9 - 0.15 * len(missing_fields))

        intent = TradeIntent(
            intent="PLACE_ORDER",
            language=language,
            confidence=round(confidence, 2),
            missing_fields=missing_fields,
            requires_confirmation=True,
            exchange="NSE",
            symbol=symbol_text,
            side=side,  # type: ignore[arg-type]
            quantity=quantity,
            order_type=order_type,  # type: ignore[arg-type]
            limit_price=price,
            product="DELIVERY",
            validity="DAY",
        )
        return TradeIntentResult(intent=intent, provider=self.name, raw_provider_output=transcript)

    async def explain_risk(self, input: RiskExplanationInput) -> str:
        prefix = {
            "hi-IN": "आपका ऑर्डर रोका गया: ",
            "hinglish": "Aapka order rok diya gaya: ",
            "en-IN": "Your order was blocked: ",
        }.get(input.language, "Your order was blocked: ")
        return f"{prefix}{input.message}"
