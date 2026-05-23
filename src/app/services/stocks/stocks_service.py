from datetime import datetime, timezone
from app.clients.alpha_vantage_client import AlphaVantageClient
from app.schemas.stocks import (
    OHLCV,
    Indicator,
    ScanFilter,
    ScanMarketResponse,
    SeriesType,
    TimeInterval,
)
from app.services.stocks.stocks_service_interface import IStocksService
from app.domain.filters import FILTERS, INDICATORS


class StocksService(IStocksService):
    def __init__(self, alphavantage_client: AlphaVantageClient) -> None:
        self.alphavantage_client = alphavantage_client

    async def get_stock_price(self, symbol: str, time_series: str) -> float:
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(
            symbol, time_series
        )
        return stock_symbol_info[0].close

    async def get_stock_indicators(
        self,
        symbol: str,
        indicators: list[Indicator],
        interval: str = TimeInterval.DAILY,
        series_type: str = SeriesType.close.name,
    ):
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(
            symbol, interval
        )
        series_prices: list[float] = [
            price.get_series(series_type) for price in stock_symbol_info
        ]

        indicator_values = {}
        for indicator in indicators:
            indicator_values[indicator.type] = INDICATORS[indicator.type.upper()](
                series_prices, indicator.time_period
            )

        return indicator_values

    async def get_stock_history(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[OHLCV]:
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(
            symbol,
        )

        return [
            ohlcv
            for ohlcv in stock_symbol_info
            if ohlcv.date >= start_date and ohlcv.date <= end_date
        ]

    async def scan_market(
        self,
        symbols: list[str],
        indicators: list[Indicator],
        filters: list[ScanFilter],
    ) -> ScanMarketResponse:
        matches = []
        for symbol in symbols:
            stock_symbol_info = await self.alphavantage_client.get_symbol_info(symbol)
            matched_symbol = {"symbol": symbol, "indicators": [], "matched_filters": []}

            if len(filters) > 0:
                filter_match = True
                for stock_filter in filters:
                    filter_match = filter_match and FILTERS[stock_filter.type](
                        stock_symbol_info, stock_filter.value
                    )

                    if not filter_match:
                        break

                    filter_key = (
                        stock_filter.type
                        if stock_filter.value is None
                        else f"{stock_filter.type}-{stock_filter.value}"
                    )
                    matched_symbol["matched_filters"].append(filter_key)

                if filter_match:
                    matched_symbol["indicators"] = self.__get_indicator_info(
                        indicators, stock_symbol_info
                    )
                    matches.append(matched_symbol)
            else:
                matched_symbol["indicators"] = self.__get_indicator_info(
                    indicators, stock_symbol_info
                )
                matches.append(matched_symbol)

        return ScanMarketResponse(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            results=matches,
            total_scanned=len(symbols),
            total_matched=len(matches),
        )

    def __get_indicator_info(
        self, indicators: list[Indicator], stock_symbol_info: list[OHLCV]
    ):
        results = []
        for indicator in indicators:
            indicator_key = indicator.type
            if indicator.time_period is not None:
                indicator_key += f"_{indicator.time_period}"
            results.append(
                {
                    indicator_key: INDICATORS[indicator.type.upper()](
                        [price.close for price in stock_symbol_info],
                        indicator.time_period,
                    )
                }
            )

        return results
