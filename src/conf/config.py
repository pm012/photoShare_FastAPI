import os
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

    # Agile logic for the local launch and Docker:
    # 1. If Docker => variable DATABASE_URL has already been provided to the system, and there's no need to search .env file.
    # 2. If we laucn locally (pytest/main.py), then the database is not in the system and Pydantic reads the local .env.
    model_config = SettingsConfigDict(
        env_file=None if os.environ.get("DATABASE_URL") else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
