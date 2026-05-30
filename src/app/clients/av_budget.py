import time
from datetime import datetime, timezone
import redis
from fastapi import HTTPException, status
from app.clients.redis_client import redis_client
from app.core.config import config
from app.core.logger import logger
from app.schemas.logger import LoggerConstants

_in_memory_minute: dict[int, int] = {}
_in_memory_day: dict[str, int] = {}


def _minute_window() -> int:
    return int(time.time() // 60)


def _day_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _in_memory_reserve() -> None:
    minute = _minute_window()
    day = _day_key()

    minute_count = _in_memory_minute.get(minute, 0) + 1
    if minute_count > config.AV_MAX_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alpha Vantage minute quota exhausted",
        )

    day_count = _in_memory_day.get(day, 0) + 1
    if day_count > config.AV_MAX_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alpha Vantage daily quota exhausted",
        )

    _in_memory_minute[minute] = minute_count
    _in_memory_day[day] = day_count


async def _redis_reserve() -> None:
    minute = _minute_window()
    day = _day_key()
    minute_redis_key = f"av_budget:minute:{minute}"
    day_redis_key = f"av_budget:day:{day}"

    minute_count = await redis_client.incr(minute_redis_key)
    if minute_count == 1:
        await redis_client.expire(minute_redis_key, 60)
    if minute_count > config.AV_MAX_PER_MINUTE:
        await redis_client.decr(minute_redis_key)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alpha Vantage minute quota exhausted",
        )

    day_count = await redis_client.incr(day_redis_key)
    if day_count == 1:
        await redis_client.expire(day_redis_key, 90000)
    if day_count > config.AV_MAX_PER_DAY:
        await redis_client.decr(minute_redis_key)
        await redis_client.decr(day_redis_key)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alpha Vantage daily quota exhausted",
        )


async def reserve_upstream_call() -> None:
    """Reserve one Alpha Vantage API call against global minute/day budgets."""
    try:
        await _redis_reserve()
    except redis.ConnectionError:
        logger.warning(LoggerConstants.CACHE_CONN_ERR)
        _in_memory_reserve()
