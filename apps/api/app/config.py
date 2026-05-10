"""Application configuration loaded from environment / .env."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://aieo:aieo@localhost:5432/aieo",
        description="SQLAlchemy database URL.",
    )
    clerk_secret_key: str = Field(default="", description="Clerk backend secret key.")
    clerk_jwt_issuer: str = Field(
        default="",
        description="Clerk JWT issuer URL, e.g. https://your-app.clerk.accounts.dev",
    )
    openai_api_key: str = Field(default="", description="Optional. Stub used when empty.")
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed origins.",
    )
    environment: str = Field(default="development")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def auth_enabled(self) -> bool:
        """Auth is enforced only when both Clerk values are set."""
        return bool(self.clerk_secret_key and self.clerk_jwt_issuer)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
