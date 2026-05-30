from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_stocks_service
from app.schemas.stocks import (
    GetStockIndicatorsRequest,
    ScanMarketRequest,
    TimeInterval,
)
from app.services.stocks.stocks_service import StocksService

stocks_router = APIRouter(prefix="/stocks")

StocksServiceDep = Annotated[StocksService, Depends(get_stocks_service)]


@stocks_router.get("/{symbol}")
async def get_symbol_price(
    symbol: str,
    stocks_service: StocksServiceDep,
    time_series: str = TimeInterval.DAILY,
):
    return await stocks_service.get_stock_price(symbol, time_series)


@stocks_router.post("/{symbol}/indicators")
async def get_stock_indicators(
    symbol: str,
    body: GetStockIndicatorsRequest,
    stocks_service: StocksServiceDep,
):
    return await stocks_service.get_stock_indicators(
        symbol, body.indicators, body.interval, body.series_type
    )


@stocks_router.get("/{symbol}/history")
async def get_stock_history(
    symbol: str,
    start_date: str,
    end_date: str,
    stocks_service: StocksServiceDep,
):
    try:
        start_date_val = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_val = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid date string")

    if start_date_val > end_date_val:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid date range")

    return await stocks_service.get_stock_history(symbol, start_date, end_date)


@stocks_router.post("/scan")
async def scan_market(body: ScanMarketRequest, stocks_service: StocksServiceDep):
    return await stocks_service.scan_market(body.symbols, body.indicators, body.filters)
