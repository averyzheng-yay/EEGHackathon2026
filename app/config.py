from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database
    database_url: str = "postgresql://localhost/olapis"

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Summarization LLM — ingestion pipeline only (provider-agnostic)
    # Currently: Cerebras free tier (~1M tokens/day). Swap base_url+model to change provider.
    summarizer_api_key: str = ""
    summarizer_base_url: str = "https://api.cerebras.ai/v1"
    summarizer_model: str = "llama3.1-8b"

    # Gemini — Ask AI chat feature only (swap these two vars to change provider)
    # Free tier: 15 RPM / 1,000 RPD (verified April 2026)
    google_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-2.5-flash-lite"

    # Ingestion
    arxiv_papers_per_category: int = 5
    ingestion_rate_limit_rpm: int = 15

    # Internal endpoint protection
    internal_api_secret: str = ""

    # CORS — comma-separated list of origins, or "*"
    allowed_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
