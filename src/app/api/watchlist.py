from fastapi import APIRouter
from app.clients.alpha_vantage_client import AlphaVantageClient
from app.service.watchlist_service import WatchlistService

watchlist_router = APIRouter(prefix='/watchlist')

alphavantage_client = AlphaVantageClient()
watchlist_service = WatchlistService(alphavantage_client)

@watchlist_router.get('/')
async def get_watchlist():
    return watchlist_service.get_items()

@watchlist_router.post('/{symbol}')
async def add_to_watchlist(symbol: str):
    return watchlist_service.add_item(symbol)

@watchlist_router.delete('/{symbol}')
async def remove_from_watchlist(symbol: str):
    return watchlist_service.remove_item(symbol)