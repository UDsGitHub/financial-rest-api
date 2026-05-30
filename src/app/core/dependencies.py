from app.clients.alpha_vantage_client import AlphaVantageClient
from app.services.market.market_service import MarketService
from app.services.stocks.stocks_service import StocksService
from app.services.watchlist.watchlist_service import WatchlistService

_alpha_vantage_client = AlphaVantageClient()
_watchlist_service = WatchlistService(_alpha_vantage_client)
_stocks_service = StocksService(_alpha_vantage_client)
_market_service = MarketService(_alpha_vantage_client, _watchlist_service)


def get_alpha_vantage_client() -> AlphaVantageClient:
    return _alpha_vantage_client


def get_watchlist_service() -> WatchlistService:
    return _watchlist_service


def get_stocks_service() -> StocksService:
    return _stocks_service


def get_market_service() -> MarketService:
    return _market_service
