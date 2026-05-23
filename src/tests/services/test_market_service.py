from unittest.mock import AsyncMock

import pytest

from app.services.market.market_service import MarketService
from tests.data.test_data import test_market_status, test_symbol_info


class TestMarketService:
    @pytest.fixture
    def fake_av(self):
        mock = AsyncMock()
        mock.get_symbol_info.return_value = test_symbol_info
        mock.get_market_status.return_value = test_market_status
        return mock

    @pytest.fixture
    def watchlist_service(self):
        mock = AsyncMock()
        mock.get_symbols.return_value = []
        return mock

    @pytest.fixture
    def service(self, fake_av, watchlist_service):
        return MarketService(fake_av, watchlist_service)

    @pytest.mark.asyncio
    async def test_get_market_status_filters_by_region(self, service, fake_av):
        response = await service.get_market_status("127.0.0.1", "United States")

        assert "United States" in response["status"]
        assert len(response["major_index_performances"]) == 3
        fake_av.get_market_status.assert_awaited_once()
