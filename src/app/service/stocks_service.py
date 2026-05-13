from app.clients.alpha_vantage_client import AlphaVantageClient
from app.schemas.stocks import Indicators, SeriesType, TimeInterval


def get_ema(
    series_prices: list[float],
    time_period: int,
):
    multiplier = 2 / (time_period + 1)
    seed_data = series_prices[-time_period:]
    previous_ema = sum(seed_data) / time_period

    for price in reversed(series_prices[:-time_period]):
        mva = (price - previous_ema) * multiplier + previous_ema
        previous_ema = mva

    return previous_ema


def get_rsi(
    series_prices: list[float],
    time_period: int,
):
    gains = []
    losses = []

    for i in range(len(series_prices) - 1):
        diff = series_prices[i] - series_prices[i + 1]
        gains.append(max(0, diff))
        losses.append(max(0, -diff))

    avg_gains = sum(gains[:time_period]) / time_period
    avg_losses = sum(losses[:time_period]) / time_period

    for i in range(time_period, len(gains)):
        avg_gains = (avg_gains * (time_period - 1) + gains[i]) / time_period
        avg_losses = (avg_losses * (time_period - 1) + losses[i]) / time_period

    if avg_losses == 0:
        avg_losses = 100

    rs = avg_gains / avg_losses
    return 100 - (100 / (1 + rs))


def get_sma(
    series_prices: list[float],
    time_period: int,
):
    return sum(series_prices[:time_period]) / time_period


indicator_methods = {
    "EMA": get_ema,
    "RSI": get_rsi,
    "SMA": get_sma,
}


class StocksService:
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
        indicators: list[str],
        time_period: int,
        interval: str = TimeInterval.DAILY,
        series_type: str = SeriesType.close,
    ):
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(
            symbol, interval
        )
        series_prices: list[float] = [price[series_type] for price in stock_symbol_info]

        indicator_values = {}
        for indicator in indicators:
            indicator_values[indicator] = indicator_methods[indicator](
                series_prices, time_period, series_type
            )

        return indicator_values

    async def get_stock_history(
        self, symbol: str, start_date: str, end_date: str
    ) -> list:
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(
            symbol,
        )

        return [price for price in stock_symbol_info if price.date >= start_date and price.date <= end_date]
