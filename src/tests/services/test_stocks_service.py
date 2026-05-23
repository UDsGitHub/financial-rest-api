from datetime import datetime

import pytest
from unittest.mock import AsyncMock

from app.schemas.stocks import Indicator, ScanFilter, SeriesType, TimeInterval
from app.services.stocks.stocks_service import StocksService
from tests.data.test_data import test_symbol_info


class TestStocksService:
    @pytest.fixture
    def fake_av(self):
        mock = AsyncMock()
        mock.get_symbol_info.return_value = test_symbol_info
        return mock

    @pytest.fixture
    def service(self, fake_av):
        return StocksService(fake_av)

    @pytest.mark.asyncio
    async def test_get_stock_price(self, service, fake_av):
        price = await service.get_stock_price("IBM", TimeInterval.DAILY)

        assert price == 218.37
        fake_av.get_symbol_info.assert_awaited_once_with("IBM", TimeInterval.DAILY)

    @pytest.mark.asyncio
    async def test_get_stock_indicators(self, service):
        indicators = await service.get_stock_indicators(
            symbol="IBM",
            indicators=[Indicator(type="EMA", time_period=20)],
            interval=TimeInterval.DAILY,
            series_type=SeriesType.close.name,
        )

        assert "EMA" in indicators
        assert indicators["EMA"] > 0

    @pytest.mark.asyncio
    async def test_get_stock_history(self, service):
        start_date = "2026-04-24"
        end_date = "2026-05-04"
        history = await service.get_stock_history("IBM", start_date, end_date)

        assert len(history) > 0

        history_start = datetime.strptime(history[0].date, "%Y-%m-%d").date()
        history_end = datetime.strptime(history[-1].date, "%Y-%m-%d").date()
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        assert start <= history_start <= end
        assert start <= history_end <= end

    @pytest.mark.asyncio
    async def test_scan_market(self, service):
        scan_result = await service.scan_market(
            ["IBM"],
            [Indicator(type="EMA", time_period=20)],
            [ScanFilter(type="price_min", value=10)],
        )

        assert scan_result.total_scanned == 1
        assert scan_result.total_matched == 1
        assert scan_result.results[0].symbol == "IBM"
