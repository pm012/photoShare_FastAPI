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

    # Pydantic Settings автоматично шукає змінні в системному оточенні (куди їх прокинув Docker)
    model_config = SettingsConfigDict(
        extra="ignore"
    )

settings = Settings()
