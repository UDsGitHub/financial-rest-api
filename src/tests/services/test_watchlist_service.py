import redis
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock
from app.core.config import config
from app.services.watchlist import watchlist_service as watchlist_module
from app.services.watchlist.watchlist_service import WatchlistService
from tests.data.test_data import test_symbol_info


@pytest.fixture(autouse=True)
def in_memory_watchlist(monkeypatch):
    mock_redis = AsyncMock()
    mock_redis.smembers.side_effect = redis.ConnectionError()
    mock_redis.sismember.side_effect = redis.ConnectionError()
    mock_redis.hset.side_effect = redis.ConnectionError()
    mock_redis.sadd.side_effect = redis.ConnectionError()
    mock_redis.unlink.side_effect = redis.ConnectionError()
    mock_redis.srem.side_effect = redis.ConnectionError()
    mock_redis.pipeline.side_effect = redis.ConnectionError()

    monkeypatch.setattr(watchlist_module, "redis_client", mock_redis)
    watchlist_module.watchlist._Watchlist__items = {}
    yield
    watchlist_module.watchlist._Watchlist__items = {}


class TestWatchlistService:
    @pytest.fixture
    def fake_av(self):
        mock = AsyncMock()
        mock.get_symbol_info.return_value = test_symbol_info
        return mock

    @pytest.fixture
    def service(self, fake_av):
        return WatchlistService(fake_av)

    @pytest.mark.asyncio
    async def test_add_item(self, service):
        response = await service.add_item("test-add", "IBM")

        assert response.symbol == "IBM"
        assert response.price == test_symbol_info[0].close

    @pytest.mark.asyncio
    async def test_get_symbols(self, service):
        await service.add_item("test-symbols", "IBM")
        response = await service.get_symbols("test-symbols")

        assert response == ["IBM"]

    @pytest.mark.asyncio
    async def test_get_items(self, service):
        await service.add_item("test-items", "IBM")
        response = await service.get_items("test-items")

        assert len(response) == 1
        assert response[0].symbol == "IBM"

    @pytest.mark.asyncio
    async def test_remove_item(self, service):
        await service.add_item("test-remove", "IBM")
        response = await service.remove_item("test-remove", "IBM")

        assert response == "IBM"
        assert await service.get_symbols("test-remove") == []

    @pytest.mark.asyncio
    async def test_add_item_rejects_when_watchlist_full(self, service):
        ip = "test-full"
        for i in range(config.MAX_WATCHLIST_SIZE):
            await service.add_item(ip, f"SYM{i}")

        with pytest.raises(HTTPException) as exc:
            await service.add_item(ip, "ONE_TOO_MANY")

        assert exc.value.status_code == 400
        assert "Watchlist limited" in exc.value.detail
