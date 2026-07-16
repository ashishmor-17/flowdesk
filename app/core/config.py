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

    # Storage Settings
    STORAGE_BACKEND: str = "local" # local or s3
    STORAGE_LOCAL_DIR: str = "uploads"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    FILES_BUCKET: str = "test-bucket"
    AWS_ENDPOINT_URL: str | None = None
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024 # 10MB default
    MIN_PART_SIZE_BYTES: int = 5 * 1024 * 1024 # 5MB default
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg,doc,docx,xls,xlsx,csv,txt,zip"

    # SMTP Email Settings
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@flowdesk.com"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()