from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from app.clients.alpha_vantage_client import AlphaVantageClient
from app.service.stocks_service import StocksService
from app.schemas.stocks import TimeInterval

stocks_router = APIRouter(prefix="/stocks")

alphavantage_client = AlphaVantageClient()
stocks_service = StocksService(alphavantage_client)


@stocks_router.get("/{symbol}")
async def get_symbol_price(symbol: str, time_series: str = TimeInterval.DAILY):
    return await stocks_service.get_stock_price(symbol, time_series)


@stocks_router.get("/indicators/{symbol}")
async def get_stock_indicators(
    symbol: str, q: Annotated[list[str], Query()] = ["EMA", "RSI", "SMA"]
):
    return await stocks_service.get_stock_indicators(symbol)


@stocks_router.get("/history/{symbol}")
async def get_stock_history(symbol: str, start_date: str, end_date: str):
    try:
        start_date_val = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_val = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Invalid date string')

    if start_date_val > end_date_val:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Invalid date range')

    return await stocks_service.get_stock_history(symbol, start_date, end_date)
