from fastapi import APIRouter, Request
from app.clients.alpha_vantage_client import AlphaVantageClient
from app.service.watchlist.watchlist_service import WatchlistService

watchlist_router = APIRouter(prefix="/watchlist")

alphavantage_client = AlphaVantageClient()
watchlist_service = WatchlistService(alphavantage_client)


@watchlist_router.get("/")
async def get_watchlist(request: Request):
    return await watchlist_service.get_items(request.client.host)


@watchlist_router.post("/{symbol}")
async def add_to_watchlist(request: Request, symbol: str):
    return await watchlist_service.add_item(request.client.host, symbol)


@watchlist_router.delete("/{symbol}")
async def remove_from_watchlist(request: Request, symbol: str):
    return await watchlist_service.remove_item(request.client.host, symbol)
