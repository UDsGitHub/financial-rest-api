import redis.asyncio as redis
from app.core.config import config

redis_client = redis.Redis(
    host=config.REDIS_URL,
    port=int(config.REDIS_PORT),
    username=config.REDIS_USERNAME,
    password=config.REDIS_PASSWORD,
    decode_responses=True,
)
