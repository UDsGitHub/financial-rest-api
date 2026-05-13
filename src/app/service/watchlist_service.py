from app.schemas.stocks import Symbol
from app.schemas.watchlist import Watchlist
from app.clients.alpha_vantage_client import AlphaVantageClient

watchlist = Watchlist()

class WatchlistService:
    def __init__(self, alphavantage_client: AlphaVantageClient):
        self.alphavantage_client = alphavantage_client

    async def get_items(self):
        return watchlist.get_items()

    async def add_item(self, item: Symbol):
        stock_symbol_info = await self.alphavantage_client.get_symbol_info()
        print(stock_symbol_info)
        return watchlist.add_item(item)

    async def remove_item(self, symbol: str):
        watchlist.remove_item(symbol)
    