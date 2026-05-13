from enum import Enum
from pydantic import BaseModel


class Market(BaseModel):
    market_type: str
    region: str
    primary_exchanges: list[str]
    local_open: str
    local_close: str
    current_status: str
    notes: str


class MarketStatus(str, Enum):
    OPEN='open'
    CLOSED='closed'


class IndexPerfomance(BaseModel):
    symbol: str
    percentage_change: str
