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


class OllamaProvider:
    """Adapter for a local Ollama server (https://ollama.com)."""

    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1",
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def _call(self, system: str, user_message: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        return data.get("message", {}).get("content", "")

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
