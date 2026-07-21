"""Central configuration read from environment variables.

This is the ONLY place API keys and other secrets are read. Never import
`os.environ` directly elsewhere in the backend, and never send any of these
values to the frontend.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "info"

    database_url: str = "postgresql+psycopg2://vaanitrade:vaanitrade_dev_password@localhost:5432/vaanitrade"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    ai_provider: str = "mock"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    local_ai_base_url: str = "http://localhost:8080/v1"
    local_ai_model: str = "local-model"
    local_ai_api_key: str = "not-needed"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    risk_max_order_value: float = 200_000
    risk_max_quantity: int = 5_000
    risk_max_price_deviation_pct: float = 5.0
    risk_daily_loss_limit: float = 25_000
    risk_duplicate_order_window_seconds: int = 10
    trading_kill_switch: bool = False

    paper_starting_balance: float = 1_000_000
    paper_slippage_bps: float = 5.0
    paper_brokerage_flat: float = 20.0
    paper_stt_rate_sell: float = 0.00025
    paper_gst_rate: float = 0.18

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def ai_provider_env(self) -> dict[str, str]:
        """Env-shaped dict handed to ai_providers.factory.create_provider."""
        return {
            "AI_PROVIDER": self.ai_provider,
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
            "ANTHROPIC_MODEL": self.anthropic_model,
            "OPENAI_API_KEY": self.openai_api_key,
            "OPENAI_MODEL": self.openai_model,
            "GEMINI_API_KEY": self.gemini_api_key,
            "GEMINI_MODEL": self.gemini_model,
            "LOCAL_AI_BASE_URL": self.local_ai_base_url,
            "LOCAL_AI_MODEL": self.local_ai_model,
            "LOCAL_AI_API_KEY": self.local_ai_api_key,
            "OLLAMA_BASE_URL": self.ollama_base_url,
            "OLLAMA_MODEL": self.ollama_model,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
