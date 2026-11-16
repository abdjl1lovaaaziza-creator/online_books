from typing import List, Set, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Telegram Bot
    BOT_TOKEN: str = Field(default="123456789:TEST_BOT_TOKEN_REPLACE_WITH_REAL", description="Telegram Bot Token")
    WEBHOOK_URL: str = Field(default="https://localhost:8000", description="Public HTTPS URL for webhooks")
    WEBHOOK_PATH: str = Field(default="/webhook", description="Path for Telegram webhook callback")
    WEBHOOK_SECRET: str = Field(default="change_this_webhook_secret_key_123456", description="Secret token for Telegram webhook validation")

    # Database & Redis
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/booklibrary",
        description="Async PostgreSQL connection string"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # Admin access
    ADMIN_IDS: str = Field(default="", description="Comma-separated Telegram user IDs of administrators")

    # External APIs
    GOOGLE_BOOKS_API_KEY: Optional[str] = Field(default=None, description="Optional Google Books API key for higher quotas")

    # Server Settings
    PORT: Optional[int] = Field(default=None, description="Railway dynamic port")
    APP_HOST: str = Field(default="0.0.0.0", description="FastAPI host")
    APP_PORT: int = Field(default=8000, description="FastAPI port")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, test, production")
    DEBUG: bool = Field(default=False, description="Debug mode")

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Ensure PostgreSQL connection string uses asyncpg driver required for async SQLAlchemy."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("APP_PORT", mode="before")
    @classmethod
    def resolve_app_port(cls, v, info) -> int:
        """Resolve dynamic port injected by cloud platforms (Railway, Render, Fly.io)."""
        import os
        port_env = os.environ.get("PORT")
        if port_env and str(port_env).isdigit():
            return int(port_env)
        return int(v) if v else 8000

    # Bot & Download System Limits
    MAX_DOWNLOAD_SIZE_MB: int = Field(default=50, description="Maximum file size to download and stream to Telegram (in MB)")
    RATE_LIMIT_CALLS: int = Field(default=10, description="Max actions permitted per period")
    RATE_LIMIT_PERIOD: int = Field(default=3, description="Rate limit period in seconds")
    SEARCH_PAGE_SIZE: int = Field(default=5, description="Number of books displayed per search page")
    DEFAULT_LANGUAGE: str = Field(default="en", description="Default user language")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "ru", "uz", "tr", "ar", "de", "fr", "es"],
        description="List of supported language codes"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def full_webhook_url(self) -> str:
        """Construct full webhook URL."""
        return f"{self.WEBHOOK_URL.rstrip('/')}{self.WEBHOOK_PATH}"

    @property
    def admin_ids_set(self) -> Set[int]:
        """Parse comma-separated admin IDs into a set of integers."""
        if not self.ADMIN_IDS:
            return set()
        ids = set()
        for item in self.ADMIN_IDS.split(","):
            cleaned = item.strip()
            if cleaned.isdigit():
                ids.add(int(cleaned))
        return ids

    def is_admin(self, telegram_id: int) -> bool:
        """Check if Telegram ID belongs to an administrator."""
        return telegram_id in self.admin_ids_set


# Global settings instance
settings = Settings()
