from fastapi import HTTPException, status
from app.schemas.stocks import Symbol
from app.schemas.watchlist import Watchlist
from app.clients.alpha_vantage_client import AlphaVantageClient

watchlist = Watchlist()


class WatchlistService:
    def __init__(self, alphavantage_client: AlphaVantageClient):
        self.alphavantage_client = alphavantage_client

    async def get_items(self):
        return watchlist.get_items()

    async def add_item(self, symbol: str):
        if watchlist.has_item(symbol):
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail=f"Symbol {symbol} already in watchlist"
            )

        symbol_info = await self.alphavantage_client.get_symbol_info(symbol)
        return watchlist.add_item(
            Symbol(symbol=symbol, price=symbol_info[0].close, date=symbol_info[0].date)
        )

    async def remove_item(self, symbol: str):
        watchlist.remove_item(symbol)
