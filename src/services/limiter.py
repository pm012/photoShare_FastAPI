from slowapi import Limiter
from slowapi.util import get_remote_address
from src.conf.config import settings

# Connect slowapi to the Docker-container Redis
# If the application is running locally, it will go to localhost, if in Docker — to the redis service
redis_auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
redis_url = f"redis://{redis_auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"

# Initialize the limiter that tracks IP addresses (get_remote_address)
# In E2E_MODE the limiter is off: UI tests log in and upload far more often than real users.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url,
    enabled=not settings.E2E_MODE,
)
