from __future__ import annotations

import httpx

from ai_providers.parsing import parse_llm_json_to_intent
from ai_providers.prompts import (
    INTENT_SYSTEM_PROMPT,
    RISK_EXPLANATION_SYSTEM_PROMPT,
    build_intent_user_message,
    build_risk_explanation_user_message,
)
from ai_providers.types import RiskExplanationInput, TradeIntentInput, TradeIntentResult

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider:
    """Adapter for Google Gemini via the generateContent REST API. Requires GEMINI_API_KEY."""

    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", timeout: float = 20.0) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required to use the gemini provider.")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def _call(self, system: str, user_message: str) -> str:
        url = f"{GEMINI_API_BASE}/{self.model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url, params={"key": self.api_key}, json=payload
            )
            response.raise_for_status()
            data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)

    async def extract_trade_intent(self, input: TradeIntentInput) -> TradeIntentResult:
        user_message = build_intent_user_message(input.transcript, input.detected_language)
        raw = await self._call(INTENT_SYSTEM_PROMPT, user_message)
        intent = parse_llm_json_to_intent(raw, input.detected_language or "en-IN")
        return TradeIntentResult(intent=intent, provider=self.name, raw_provider_output=raw)

    async def explain_risk(self, input: RiskExplanationInput) -> str:
        user_message = build_risk_explanation_user_message(
            input.risk_code, input.message, input.language
        )
        return await self._call(RISK_EXPLANATION_SYSTEM_PROMPT, user_message)
