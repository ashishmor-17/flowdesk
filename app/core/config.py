from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import SecretStr

class Settings(BaseSettings):
    """Application settings."""

    DATABASE_URL: SecretStr
    JWT_SECRET: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRY: int = 15 #minutes
    REFRESH_TOKEN_EXPIRY: int = 7 #days
    REDIS_URL: str

    ENVIRONMENT: str = "development"
    RATE_LIMIT_ENABLED: bool = True
    REDIS_PREFIX: str = "flowdesk"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()