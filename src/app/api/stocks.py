from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.clients.alpha_vantage_client import AlphaVantageClient
from app.service.stocks_service import StocksService
from app.schemas.stocks import Indicator, TimeInterval

stocks_router = APIRouter(prefix="/stocks")

alphavantage_client = AlphaVantageClient()
stocks_service = StocksService(alphavantage_client)


@stocks_router.get("/{symbol}")
async def get_symbol_price(symbol: str, time_series: str = TimeInterval.DAILY):
    return await stocks_service.get_stock_price(symbol, time_series)


@stocks_router.post("/indicators/{symbol}")
async def get_stock_indicators(
    symbol: str, indicators: list[Indicator], interval: str, series_type: str
):
    return await stocks_service.get_stock_indicators(
        symbol, indicators, interval, series_type
    )


@stocks_router.get("/history/{symbol}")
async def get_stock_history(symbol: str, start_date: str, end_date: str):
    try:
        start_date_val = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_val = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid date string")

    if start_date_val > end_date_val:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid date range")

    return await stocks_service.get_stock_history(symbol, start_date, end_date)


@stocks_router.post("/scan")
async def scan_market(
    symbols: list[str], indicators: list[Indicator], filters: list[str]
):
    matches = await stocks_service.scan_market(symbols, indicators, filters)
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": matches,
        "total_scanned": len(symbols),
        "total_matched": len(matches),
    }
