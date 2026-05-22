from datetime import datetime, timedelta
import time
from fastapi import Request
from fastapi.responses import JSONResponse
import redis
from starlette.middleware.base import BaseHTTPMiddleware
from app.clients.redis_client import redis_client
from app.core.logger import logger
from app.schemas.logger import LoggerConstants

MAX_REQUESTS = 25
TTL = 60
limits: dict[str, list[datetime]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):

    async def redis_rate_limit(self, ip: str) -> bool:
        current_window = int(time.time() // TTL)
        key = f"rate_limit:{ip}:{current_window}"

        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, TTL)
        if count > MAX_REQUESTS:
            return False
        return True

    def in_memory_rate_limit(self, ip: str) -> bool:
        curr = datetime.now()

        if ip not in limits:
            limits[ip] = [curr]
            return True

        window_start = curr - timedelta(seconds=TTL)
        limits[ip] = [t for t in limits[ip] if t > window_start]

        if len(limits[ip]) < MAX_REQUESTS:
            limits[ip].append(curr)
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
