import redis.asyncio as redis
from app.config import config

redis_client = redis.Redis(
    host=config.REDIS_URL,
    port=config.REDIS_PORT,
    username=config.REDIS_USERNAME,
    password=config.REDIS_PASSWORD,
    decode_responses=True,
)