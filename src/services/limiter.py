from slowapi import Limiter
from slowapi.util import get_remote_address
from src.conf.config import settings

# Підключаємо slowapi до нашого Docker-контейнера Redis
# Якщо додаток запущено локально, він піде на localhost, якщо в Docker — на сервіс redis
redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"

# Ініціалізуємо лімітер, який трекає IP-адреси (get_remote_address)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url
)
