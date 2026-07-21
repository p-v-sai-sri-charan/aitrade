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

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider:
    """Adapter for OpenAI's Chat Completions API. Requires OPENAI_API_KEY."""

    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 20.0) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to use the openai provider.")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def _call(self, system: str, user_message: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]

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
