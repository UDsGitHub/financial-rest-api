import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

import app.clients.av_budget as av_budget_module
from app.clients.av_budget import reserve_upstream_call
from app.core.config import config


@pytest.fixture(autouse=True)
def reset_in_memory_budget():
    av_budget_module._in_memory_minute.clear()
    av_budget_module._in_memory_day.clear()
    yield
    av_budget_module._in_memory_minute.clear()
    av_budget_module._in_memory_day.clear()


@pytest.fixture
def mock_redis_down(monkeypatch):
    mock_redis = AsyncMock()
    import redis

    mock_redis.incr.side_effect = redis.ConnectionError()
    monkeypatch.setattr(av_budget_module, "redis_client", mock_redis)


@pytest.mark.asyncio
async def test_reserve_allows_calls_under_limit(mock_redis_down):
    for _ in range(config.AV_MAX_PER_MINUTE):
        await reserve_upstream_call()


@pytest.mark.asyncio
async def test_reserve_rejects_minute_quota(mock_redis_down):
    for _ in range(config.AV_MAX_PER_MINUTE):
        await reserve_upstream_call()

    with pytest.raises(HTTPException) as exc:
        await reserve_upstream_call()

    assert exc.value.status_code == 503
    assert "minute quota" in exc.value.detail


@pytest.mark.asyncio
async def test_reserve_rejects_daily_quota(mock_redis_down, monkeypatch):
    monkeypatch.setattr(config, "AV_MAX_PER_MINUTE", 100)
    monkeypatch.setattr(config, "AV_MAX_PER_DAY", 2)

    await reserve_upstream_call()
    await reserve_upstream_call()

    with pytest.raises(HTTPException) as exc:
        await reserve_upstream_call()

    assert exc.value.status_code == 503
    assert "daily quota" in exc.value.detail
