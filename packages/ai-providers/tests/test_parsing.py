from ai_providers.parsing import parse_llm_json_to_intent


def test_parses_valid_json():
    raw = """{
      "intent": "PLACE_ORDER",
      "exchange": "NSE",
      "symbol": "Reliance",
      "side": "BUY",
      "quantity": 10,
      "orderType": "LIMIT",
      "limitPrice": 2950,
      "product": "DELIVERY",
      "validity": "DAY",
      "language": "hinglish",
      "confidence": 0.95,
      "missingFields": [],
      "requiresConfirmation": true,
      "ambiguousSymbolCandidates": null,
      "orderId": null
    }"""
    intent = parse_llm_json_to_intent(raw)
    assert intent.intent == "PLACE_ORDER"
    assert intent.symbol == "Reliance"
    assert intent.quantity == 10
    assert intent.limit_price == 2950


def test_strips_markdown_fences():
    raw = '```json\n{"intent": "VIEW_PORTFOLIO", "language": "en-IN", "confidence": 0.9}\n```'
    intent = parse_llm_json_to_intent(raw)
    assert intent.intent == "VIEW_PORTFOLIO"


def test_degrades_gracefully_on_garbage():
    intent = parse_llm_json_to_intent("not json at all")
    assert intent.intent == "UNKNOWN"
    assert intent.confidence == 0.0


def test_rejects_invalid_enum_values():
    raw = '{"intent": "DO_SOMETHING_BAD", "side": "HOLD", "language": "klingon", "confidence": 5}'
    intent = parse_llm_json_to_intent(raw, fallback_language="en-IN")
    assert intent.intent == "UNKNOWN"
    assert intent.side is None
    assert intent.language == "en-IN"
    assert intent.confidence == 1.0  # clamped
