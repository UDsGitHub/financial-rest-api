from pydantic import BaseModel

class Symbol(BaseModel):
    symbol: str
    price: float
    date: str

class TimeSeries:
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    MONTHLY = 'MONTHLY'

    value_map = {
        DAILY: 'TIME_SERIES_DAILY',
        WEEKLY: 'TIME_SERIES_WEEKLY',
        MONTHLY: 'TIME_SERIES_MONTHLY',
    }

class OHLCV(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    date: str

