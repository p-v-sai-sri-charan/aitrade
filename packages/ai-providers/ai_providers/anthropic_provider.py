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

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider:
    """Adapter for Anthropic Claude via the Messages API. Requires ANTHROPIC_API_KEY."""

    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-5", timeout: float = 20.0) -> None:
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required to use the anthropic provider.")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def _call(self, system: str, user_message: str, max_tokens: int = 512) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user_message}],
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        parts = data.get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")

    async def extract_trade_intent(self, input: TradeIntentInput) -> TradeIntentResult:
        user_message = build_intent_user_message(input.transcript, input.detected_language)
        raw = await self._call(INTENT_SYSTEM_PROMPT, user_message)
        intent = parse_llm_json_to_intent(raw, input.detected_language or "en-IN")
        return TradeIntentResult(intent=intent, provider=self.name, raw_provider_output=raw)

    async def explain_risk(self, input: RiskExplanationInput) -> str:
        user_message = build_risk_explanation_user_message(
            input.risk_code, input.message, input.language
        )
        return await self._call(RISK_EXPLANATION_SYSTEM_PROMPT, user_message, max_tokens=200)
