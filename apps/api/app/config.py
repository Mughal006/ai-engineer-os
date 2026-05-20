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
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider: 'ollama' (local) or 'stub' (deterministic, used in tests).",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the local Ollama API.",
    )
    llm_model: str = Field(
        default="llama3.2:3b",
        description="Default chat model. Must be pulled on the Ollama host.",
    )
    llm_timeout_seconds: float = Field(default=120.0)
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
