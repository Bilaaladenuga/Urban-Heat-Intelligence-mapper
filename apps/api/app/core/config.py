"""Application configuration loaded from environment variables / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Urban Heat Intelligence API"
    environment: str = "development"  # development | staging | production
    api_v1_prefix: str = "/api/v1"

    # Comma-separated list of allowed CORS origins, e.g. "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"

    # --- Database (introduced in Task 1.3/1.4 — Supabase + PostGIS) ---
    # Leave unset until the Supabase connection task; the API runs without them.
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_db_url: str | None = None  # Postgres connection string (PostGIS)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
