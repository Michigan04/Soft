from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://risk_platform:risk_platform_dev_password@localhost:5432/risk_platform"

    JWT_SECRET_KEY: str = "change-this-dev-secret-please"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5530,http://127.0.0.1:5530"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_ADDRESS: str = "no-reply@iitm-risk-platform.dev"
    SMTP_USE_TLS: bool = True

    ENVIRONMENT: str = "development"
    ENABLE_DEMO_ACCOUNTS: bool = True

    # Set automatically by Vercel at runtime; switches the DB engine to serverless-friendly pooling.
    VERCEL: bool = False

    @field_validator("DATABASE_URL")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        # Hosted Postgres providers (Neon, Vercel Postgres, Supabase) hand out postgres:// or
        # postgresql:// URLs, which SQLAlchemy would route to psycopg2; this project ships psycopg 3.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
