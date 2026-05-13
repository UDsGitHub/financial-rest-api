from app.clients.alpha_vantage_client import AlphaVantageClient
from app.schemas.stocks import OHLCV, Indicator, SeriesType, TimeInterval


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
    time_period: int = 14,
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


def price_min_check(series_prices: list[OHLCV], val: float | None = None):
    if val is None:
        return False
    return series_prices[0].close >= val


def price_max_check(series_prices: list[OHLCV], val: float | None = None):
    if val is None:
        return False
    return series_prices[0].close <= val


def volume_min_check(series_prices: list[OHLCV], val: float | None = None):
    if val is None:
        return False
    return series_prices[0].volume >= val


def perc_change_min_check(series_prices: list[OHLCV], val: float | None = None):
    if val is None:
        return False
    change = series_prices[0].close - series_prices[1].close
    if series_prices[1].close == 0:
        perc_change = 0
    else:
        perc_change = (change / series_prices[1].close) * 100
    return abs(perc_change) >= val


def perc_change_max_check(series_prices: list[OHLCV], val: float | None = None):
    if val is None:
        return False
    change = series_prices[0].close - series_prices[1].close
    if series_prices[1].close == 0:
        perc_change = 0
    else:
        perc_change = (change / series_prices[1].close) * 100
    return abs(perc_change) <= val


def above_ema_20_check(series_prices: list[OHLCV], val: float | None = None):
    ema = get_ema([price.close for price in series_prices], 20)
    return series_prices[0].close > ema


def above_sma_50_check(series_prices: list[OHLCV], val: float | None = None):
    sma = get_sma([price.close for price in series_prices], 50)
    return series_prices[0].close > sma


def ema_crossover_check(series_prices: list[OHLCV], val: float | None = None):
    fast_ema = get_ema([price.close for price in series_prices], 12)
    slow_ema = get_ema([price.close for price in series_prices], 26)
    return fast_ema > slow_ema


indicator_methods = {
    "EMA": get_ema,
    "RSI": get_rsi,
    "SMA": get_sma,
}

filter_methods = {
    "price_min": price_min_check,
    "price_max": price_max_check,
    "volume_min": volume_min_check,
    "perc_change_min": perc_change_min_check,
    "perc_change_max": perc_change_max_check,
    "above_ema_20": above_ema_20_check,
    "above_sma_50": above_sma_50_check,
    "ema_crossover": ema_crossover_check,
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
        interval: str = TimeInterval.DAILY,
        series_type: str = SeriesType.close,
    ):
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(
            symbol, interval
        )
        series_prices: list[float] = [price[series_type] for price in stock_symbol_info]

        indicator_values = {}
        for indicator in indicators:
            indicator_values[indicator.type] = indicator_methods[indicator.type](
                series_prices, indicator.time_period, series_type
            )

        return indicator_values

    async def get_stock_history(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[OHLCV]:
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(
            symbol,
        )

        return [
            price
            for price in stock_symbol_info
            if price.date >= start_date and price.date <= end_date
        ]

    async def scan_market(
        self, symbols: list[str], indicators: list[Indicator], filters: list[str]
    ) -> list:
        matches = []
        for symbol in symbols:
            stock_symbol_info = await self.alphavantage_client.get_symbol_info(symbol)
            matched_symbol = {"symbol": symbol, "indicators": [], "matched_filters": []}

            for indicator in indicators:
                indicator_key = indicator.type
                if indicator.time_period is not None:
                    indicator_key += f"_{indicator.time_period}"
                matched_symbol["indicators"].append(
                    {
                        indicator_key: indicator_methods[indicator.type](
                            [price.close for price in stock_symbol_info],
                            indicator.time_period,
                        )
                    }
                )

            filter_match = False
            for stock_filter in filters:
                filter_match = filter_match and filter_methods[filter](
                    stock_symbol_info
                )
                matched_symbol["matched_filters"].append(stock_filter)

            if filter_match:
                matches.append(matched_symbol)

        return matches
