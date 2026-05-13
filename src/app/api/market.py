from fastapi import APIRouter

from app.clients.alpha_vantage_client import AlphaVantageClient
from app.service.market_service import MarketService
from app.service.watchlist_service import WatchlistService

market_router = APIRouter(prefix='/market')

alphavantage_client = AlphaVantageClient()
watchlist_service = WatchlistService(alphavantage_client)
market_service = MarketService(alphavantage_client, watchlist_service)

@market_router.get('/status')
async def get_market_status(region: str | None = None):
    return await market_service.get_market_status(region)