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
    redis_lock_ttl_seconds: int = 5

    # Discovery & Geolocation
    nearby_radius_km: float = 5.0

    # Image Storage (Azure Blob)
    azure_storage_connection_string: str = ""
    azure_storage_container_name: str = "offer-images"
    azure_storage_base_url: str = ""

    # Rate Limiting
    rate_limit_max_requests: int = 10
    rate_limit_window_seconds: int = 60

    # Background Jobs
    expiration_check_interval_seconds: int = 60

    # Admin User IDs (comma-separated)
    admin_telegram_ids: str = ""

    # Logging
    log_level: str = "INFO"

    # Application
    app_name: str = "telegram-marketplace"
    environment: str = "development"

    # Health server
    health_host: str = "127.0.0.1"
    health_port: int = 8000

    @property
    def admin_user_ids(self) -> list[int]:
        """Parse admin user IDs from comma-separated string."""
        if not self.admin_telegram_ids:
            return []
        return [int(uid.strip()) for uid in self.admin_telegram_ids.split(",")]


def load_settings() -> Settings:
    """Load and validate settings from environment."""
    return Settings()  # type: ignore[call-arg]
