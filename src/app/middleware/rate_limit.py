from datetime import datetime, timedelta
import time
from fastapi import Request
from fastapi.responses import JSONResponse
import redis
from starlette.middleware.base import BaseHTTPMiddleware
from app.clients.redis_client import redis_client
from app.core.config import config
from app.core.logger import logger
from app.schemas.logger import LoggerConstants


class RateLimitMiddleware(BaseHTTPMiddleware):

    limits: dict[str, list[datetime]] = {}


    async def redis_rate_limit(self, ip: str) -> bool:
        current_window = int(time.time() // config.RATE_LIMIT_WINDOW)
        key = f"rate_limit:{ip}:{current_window}"

        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, config.RATE_LIMIT_WINDOW)
        if count > config.MAX_REQUESTS_PER_MINUTE:
            return False
        return True

    def in_memory_rate_limit(self, ip: str) -> bool:
        curr = datetime.now()

        if ip not in self.limits:
            self.limits[ip] = [curr]
            return True

        window_start = curr - timedelta(seconds=config.RATE_LIMIT_WINDOW)
        self.limits[ip] = [t for t in self.limits[ip] if t > window_start]

        if len(self.limits[ip]) < config.MAX_REQUESTS_PER_MINUTE:
            self.limits[ip].append(curr)
            return True

        return False

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host

        try:
            allowed = await self.redis_rate_limit(ip)
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)

            allowed = self.in_memory_rate_limit(ip)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        return await call_next(request)
