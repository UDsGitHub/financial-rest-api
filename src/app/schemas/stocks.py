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


class OHLCV(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    date: str


class SeriesType(str, Enum):
    open = "open"
    high = "high"
    low = "low"
    close = "close"


class Indicators(BaseModel):
    EMA: float | None = None
    RSI: float | None = None
    SMA: float | None = None