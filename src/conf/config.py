import os
from urllib.parse import urlsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 465
    MAIL_SERVER: str
    MAIL_CONFIRMATION_REQUIRED: bool = True # set to True for production (can be switched off in the  .env file)
    PUBLIC_API_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024
    MAX_AVATAR_SIZE_BYTES: int = 2 * 1024 * 1024

    # UI-test mode (never enable in production): rate limiter off, fake photo/avatar storage
    # instead of Cloudinary, no real e-mails, extra /e2e/info endpoint. See src/services/e2e.py.
    E2E_MODE: bool = False

    # Agile logic for the local launch and Docker:
    # 1. If Docker => variable DATABASE_URL has already been provided to the system, and there's no need to search .env file.
    # 2. If we laucn locally (pytest/main.py), then the database is not in the system and Pydantic reads the local .env.
    model_config = SettingsConfigDict(
        env_file=None if os.environ.get("DATABASE_URL") else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def _e2e_mode_requires_dedicated_database(self):
        # Safety net: fake storage + disabled limiter must never run against a real database.
        if self.E2E_MODE:
            db_name = urlsplit(self.DATABASE_URL).path.lstrip("/")
            if not db_name.endswith("_e2e"):
                raise ValueError("E2E_MODE=true requires a DATABASE_URL whose database name ends with '_e2e'")
        return self


settings = Settings()
