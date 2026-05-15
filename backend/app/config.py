"""Pydantic settings for the AI Safety Dashboard backend."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ─── Database ───
    DATABASE_URL: str = "postgresql+asyncpg://admin:changeme@localhost:5432/ai_safety"

    # ─── Redis ───
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── JWT ───
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── LLM Providers ───
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ─── Scanner Thresholds ───
    INJECTION_THRESHOLD: float = 0.85
    TOXICITY_THRESHOLD: float = 0.7
    HALLUCINATION_THRESHOLD: float = 0.6
    BIAS_THRESHOLD: float = 0.6

    # ─── Scanner Mode ───
    SCANNER_MODE: str = "lightweight"  # "lightweight" or "full"

    # ─── App ───
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    DEFAULT_RATE_LIMIT: int = 100

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
