from app.schemas.stocks import OHLCV, ScanFilterType
from app.domain.indicators import INDICATORS, IndicatorType


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
    ema = INDICATORS[IndicatorType.EMA]([price.close for price in series_prices], 20)
    return series_prices[0].close > ema


def above_sma_50_check(series_prices: list[OHLCV], val: float | None = None):
    sma = INDICATORS[IndicatorType.SMA]([price.close for price in series_prices], 50)
    return series_prices[0].close > sma


def ema_crossover_check(series_prices: list[OHLCV], val: float | None = None):
    fast_ema = INDICATORS[IndicatorType.EMA]([price.close for price in series_prices], 12)
    slow_ema = INDICATORS[IndicatorType.EMA]([price.close for price in series_prices], 26)
    return fast_ema > slow_ema


FILTERS: dict[ScanFilterType, callable] = {
    ScanFilterType.price_min: price_min_check,
    ScanFilterType.price_max: price_max_check,
    ScanFilterType.volume_min: volume_min_check,
    ScanFilterType.perc_change_min: perc_change_min_check,
    ScanFilterType.perc_change_max: perc_change_max_check,
    ScanFilterType.above_ema_20: above_ema_20_check,
    ScanFilterType.above_sma_50: above_sma_50_check,
    ScanFilterType.ema_crossover: ema_crossover_check,
}
