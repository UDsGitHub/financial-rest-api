from enum import Enum
from pydantic import BaseModel


class Symbol(BaseModel):
    symbol: str
    price: float
    date: str


class TimeInterval(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


TIME_SERIES_FUNCTIONS = {
    TimeInterval.DAILY: "TIME_SERIES_DAILY",
    TimeInterval.WEEKLY: "TIME_SERIES_WEEKLY",
    TimeInterval.MONTHLY: "TIME_SERIES_MONTHLY",
}


class SeriesType(str, Enum):
    open = "open"
    high = "high"
    low = "low"
    close = "close"
    volume = "volume"


class OHLCV(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    date: str

    def get_series(self, series_type: SeriesType):
        match series_type:
            case SeriesType.open:
                return self.open
            case SeriesType.high:
                return self.high
            case SeriesType.low:
                return self.low
            case SeriesType.close:
                return self.close
            case SeriesType.volume:
                return self.volume


class IndicatorType(str, Enum):
    EMA = "EMA"
    RSI = "RSI"
    SMA = "SMA"


class ScanFilterType(str, Enum):
    price_min = "price_min"
    price_max = "price_max"
    volume_min = "volume_min"
    perc_change_min = "perc_change_min"
    perc_change_max = "perc_change_max"
    above_ema_20 = "above_ema_20"
    above_sma_50 = "above_sma_50"
    ema_crossover = "ema_crossover"


class Indicator(BaseModel):
    type: IndicatorType
    time_period: int | None = None


class ScanFilter(BaseModel):
    type: ScanFilterType
    value: float | None = None


class GetStocksPriceResponse(BaseModel):
    symbol: str
    price: float


class GetStockIndicatorsRequest(BaseModel):
    indicators: list[Indicator]
    interval: TimeInterval = TimeInterval.DAILY
    series_type: SeriesType = SeriesType.close


class ScanMarketRequest(BaseModel):
    symbols: list[str]
    indicators: list[Indicator]
    filters: list[ScanFilter]


class ScanMarketMatchedResult(BaseModel):
    symbol: str
    indicators: list
    matched_filters: list


class ScanMarketResponse(BaseModel):
    timestamp: str
    results: list[ScanMarketMatchedResult]
    total_scanned: int
    total_matched: int
