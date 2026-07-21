"""The provider-neutral AI interface.

Every adapter (Anthropic, OpenAI, Gemini, local OpenAI-compatible, Ollama,
and the offline Mock provider) implements this Protocol. The AI model may
ONLY extract intent, identify missing information, translate/normalize
commands, or explain validation errors -- it must never place an order or
be trusted without independent backend schema validation.

Do not import a specific provider SDK anywhere outside this package.
"""

from __future__ import annotations

from typing import Protocol

from ai_providers.types import RiskExplanationInput, TradeIntentInput, TradeIntentResult


class AIProvider(Protocol):
    name: str

    async def extract_trade_intent(self, input: TradeIntentInput) -> TradeIntentResult: ...

    async def explain_risk(self, input: RiskExplanationInput) -> str: ...
