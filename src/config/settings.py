"""Configuration settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot
    bot_token: str

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Stripe
    stripe_secret_key: str
    stripe_price_mapping: str = "{}"  # JSON string mapping

    # Logging
    log_level: str = "INFO"

    # Application
    app_name: str = "telegram-marketplace"
    environment: str = "development"


def load_settings() -> Settings:
    """Load and validate settings from environment."""
    return Settings()  # type: ignore[call-arg]
