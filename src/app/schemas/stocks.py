from enum import Enum
from pydantic import BaseModel


class Symbol(BaseModel):
    symbol: str
    price: float
    date: str


class TimeInterval:
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

    value_map = {
        DAILY: "TIME_SERIES_DAILY",
        WEEKLY: "TIME_SERIES_WEEKLY",
        MONTHLY: "TIME_SERIES_MONTHLY",
    }


class SeriesType(str, Enum):
    open = "open"
    high = "high"
    low = "low"
    close = "close"


class OHLCV(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    date: str

    def get_series(self, series_type: str):
        match series_type:
            case SeriesType.open.name:
                return self.open
            case SeriesType.high.name:
                return self.high
            case SeriesType.low.name:
                return self.low
            case SeriesType.close.name:
                return self.close
            case SeriesType.volume.name:
                return self.volume


class Indicator(BaseModel):
    type: str
    time_period: int | None = None


class GetStockIndicatorsRequest(BaseModel):
    indicators: list[Indicator]
    interval: str = TimeInterval.DAILY
    series_type: str = SeriesType.close.name


class ScanMarketRequest(BaseModel):
    symbols: list[str]
    indicators: list[Indicator]
    filters: list[str]


class ScanMarketMatchedResult(BaseModel):
    symbol: str
    indicators: list
    matched_filters: list


class ScanMarketResponse(BaseModel):
    timestamp: str
    results: list[ScanMarketMatchedResult]
    total_scanned: int
    total_matched: int
