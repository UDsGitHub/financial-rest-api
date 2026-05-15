import time
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.clients.redis_client import redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        current_window = int(time.time() // 60)
        key = f"rate_limit:{ip}:{current_window}"

        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)
        if count > 25:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        return await call_next(request)
