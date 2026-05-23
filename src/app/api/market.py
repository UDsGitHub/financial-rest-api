from fastapi import APIRouter, Request
from app.clients.alpha_vantage_client import AlphaVantageClient
from app.services.market.market_service import MarketService
from app.services.watchlist.watchlist_service import WatchlistService

market_router = APIRouter(prefix="/market")

alphavantage_client = AlphaVantageClient()
watchlist_service = WatchlistService(alphavantage_client)
market_service = MarketService(alphavantage_client, watchlist_service)


@market_router.get("/status")
async def get_market_status(request: Request, region: str | None = None):
    return await market_service.get_market_status(request.client.host, region)
