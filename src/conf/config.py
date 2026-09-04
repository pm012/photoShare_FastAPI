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

    # Гнучка логіка для локального запуску та Docker:
    # 1. Якщо ми в Docker, змінна DATABASE_URL вже є в системі, і ми НЕ шукаємо файл .env.
    # 2. Якщо ми запускаємо локально (pytest/main.py), бази в системі немає, і Pydantic зчитує наш локальний .env.
    model_config = SettingsConfigDict(
        env_file=None if os.environ.get("DATABASE_URL") else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
