import redis
from src.conf.config import settings

class TokenBlacklistService:
    def __init__(self):
        # Підключаємося до контейнера Redis за параметрами з .env
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )

    def add_to_blacklist(self, token: str, expire_time_seconds: int):
        # Зберігаємо токен у Redis. Коли час TTL мине, Redis сам його видалить
        self.redis_client.setex(name=token, time=expire_time_seconds, value="blacklisted")

    def is_token_blacklisted(self, token: str) -> bool:
        # Перевіряємо, чи є такий токен у чорному списку
        return self.redis_client.exists(token) == 1

blacklist_service = TokenBlacklistService()
