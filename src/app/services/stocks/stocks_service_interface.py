from abc import ABC, abstractmethod
from app.schemas.stocks import (
    OHLCV,
    Indicator,
    ScanMarketResponse,
    SeriesType,
    TimeInterval,
)


class IStocksService(ABC):
    @abstractmethod
    async def get_stock_price(self, symbol: str, time_series: str) -> float:
        pass

    @abstractmethod
    async def get_stock_indicators(
        self,
        symbol: str,
        indicators: list[Indicator],
        interval: str = TimeInterval.DAILY,
        series_type: str = SeriesType.close.name,
    ):
        pass

    @abstractmethod
    async def get_stock_history(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[OHLCV]:
        pass

    @abstractmethod
    async def scan_market(
        self, symbols: list[str], indicators: list[Indicator], filters: list[str]
    ) -> ScanMarketResponse:
        pass
