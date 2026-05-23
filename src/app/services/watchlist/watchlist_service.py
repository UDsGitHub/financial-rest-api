from fastapi import HTTPException, status
import redis
from app.schemas.stocks import Symbol
from app.schemas.watchlist import Watchlist
from app.clients.alpha_vantage_client import AlphaVantageClient
from app.clients.redis_client import redis_client
from app.core.logger import logger
from app.schemas.logger import LoggerConstants
from app.services.watchlist.watchlist_service_interface import IWatchlistService

watchlist = Watchlist()


class WatchlistService(IWatchlistService):
    def __init__(self, alphavantage_client: AlphaVantageClient):
        self.alphavantage_client = alphavantage_client

    def get_watchlist_key(self, ip: str):
        return f"users:{ip}:watchlist"

    async def get_symbols(self, ip: str) -> list[str]:
        key = self.get_watchlist_key(ip)
        try:
            symbols = await redis_client.smembers(f"{key}:list")
            return list(symbols)
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)
            return watchlist.get_symbols(ip)

    async def get_items(self, ip: str):
        key = self.get_watchlist_key(ip)
        try:
            item_ids = await redis_client.smembers(f"{key}:list")
            pipe = await redis_client.pipeline()
            if item_ids:
                for id in item_ids:
                    pipe.hgetall(f"{key}:set:{id}")
            results = await pipe.execute()

            items = []
            for result in results:
                symbol_info = await self.alphavantage_client.get_symbol_info(
                    result["symbol"]
                )
                item = Symbol(
                    symbol=result["symbol"],
                    price=symbol_info[0].close,
                    date=result["date"],
                )
                items.append(item)
            return items
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)
            items = watchlist.get_items(ip)
        return items

    async def add_item(self, ip: str, symbol: str):
        key = self.get_watchlist_key(ip)
        try:
            has_symbol = await redis_client.sismember(f"{key}:list", symbol)
            if has_symbol:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail=f"Symbol {symbol} already in watchlist",
                )

            symbol_info = await self.alphavantage_client.get_symbol_info(symbol)
            await redis_client.hset(
                f"{key}:set:{symbol}",
                mapping={
                    "symbol": symbol,
                    "price": symbol_info[0].close,
                    "date": symbol_info[0].date,
                },
            )
            await redis_client.sadd(f"{key}:list", symbol)
            return Symbol(
                symbol=symbol,
                price=symbol_info[0].close,
                date=symbol_info[0].date,
            )
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)

            if watchlist.has_item(ip, symbol):
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail=f"Symbol {symbol} already in watchlist",
                )
            symbol_info = await self.alphavantage_client.get_symbol_info(symbol)
            return watchlist.add_item(
                ip,
                Symbol(
                    symbol=symbol, price=symbol_info[0].close, date=symbol_info[0].date
                ),
            )

    async def remove_item(self, ip: str, symbol: str):
        key = self.get_watchlist_key(ip)
        try:
            has_symbol = await redis_client.sismember(f"{key}:list", symbol)
            if has_symbol:
                await redis_client.unlink(f"{key}:set:{symbol}")
                await redis_client.srem(f"{key}:list", symbol)
            return symbol
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)

            return watchlist.remove_item(ip, symbol)
