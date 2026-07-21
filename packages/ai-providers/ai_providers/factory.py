"""Builds the active AIProvider from configuration.

The active provider is selected by the `AI_PROVIDER` environment variable
(mock | anthropic | openai | gemini | local | ollama). No UI component or
trading service should ever import a specific adapter directly -- only this
factory (wired in apps/api/app/deps.py).
"""

from __future__ import annotations

import os

from ai_providers.anthropic_provider import AnthropicProvider
from ai_providers.base import AIProvider
from ai_providers.gemini_provider import GeminiProvider
from ai_providers.local_openai_compatible_provider import LocalOpenAICompatibleProvider
from ai_providers.mock_provider import MockProvider
from ai_providers.ollama_provider import OllamaProvider
from ai_providers.openai_provider import OpenAIProvider

SUPPORTED_PROVIDERS = {"mock", "anthropic", "openai", "gemini", "local", "ollama"}


def create_provider(provider_name: str | None = None, env: dict[str, str] | None = None) -> AIProvider:
    env = env if env is not None else dict(os.environ)
    name = (provider_name or env.get("AI_PROVIDER") or "mock").strip().lower()

    if name not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown AI_PROVIDER '{name}'. Supported: {sorted(SUPPORTED_PROVIDERS)}"
        )

    if name == "mock":
        return MockProvider()

    if name == "anthropic":
        return AnthropicProvider(
            api_key=env.get("ANTHROPIC_API_KEY", ""),
            model=env.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        )

    if name == "openai":
        return OpenAIProvider(
            api_key=env.get("OPENAI_API_KEY", ""),
            model=env.get("OPENAI_MODEL", "gpt-4o-mini"),
        )

    if name == "gemini":
        return GeminiProvider(
            api_key=env.get("GEMINI_API_KEY", ""),
            model=env.get("GEMINI_MODEL", "gemini-1.5-flash"),
        )

    if name == "local":
        return LocalOpenAICompatibleProvider(
            base_url=env.get("LOCAL_AI_BASE_URL", "http://localhost:8080/v1"),
            model=env.get("LOCAL_AI_MODEL", "local-model"),
            api_key=env.get("LOCAL_AI_API_KEY", "not-needed"),
        )

    if name == "ollama":
        return OllamaProvider(
            base_url=env.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=env.get("OLLAMA_MODEL", "llama3.1"),
        )

    raise AssertionError("unreachable")
