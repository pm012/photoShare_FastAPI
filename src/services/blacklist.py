import redis
from src.conf.config import settings

class TokenBlacklistService:
    def __init__(self):
        # Initialising connection to the Redis container with parameters from .env
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

    def add_to_blacklist(self, token: str, expire_time_seconds: int):
        # Storing the token in Redis. When the TTL time expires, Redis will automatically delete it
        self.redis_client.setex(name=token, time=expire_time_seconds, value="blacklisted")

    def is_token_blacklisted(self, token: str) -> bool:
        # Checking if the token is in the blacklist
        return self.redis_client.exists(token) == 1

blacklist_service = TokenBlacklistService()
