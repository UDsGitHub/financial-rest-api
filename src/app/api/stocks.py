from typing import Annotated
from fastapi import APIRouter, Query

stocks_router = APIRouter(prefix='/stocks')

@stocks_router.get('/{symbol}')
async def get_symbol_price(symbol: str):
    return {"my": "symbol"}

@stocks_router.get('/indicators/{symbol}')
async def get_stock_indicators(symbol: str, q: Annotated[list[str], Query()] = ['EMA', 'RSI', 'SMA']):
    return {"my": "indicators"}

@stocks_router.get('/history/{symbol}')
async def get_stock_history(symbol: str):
    return {"my": "history"}