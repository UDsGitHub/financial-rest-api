from app.clients.alpha_vantage_client import AlphaVantageClient
from app.schemas.market import IndexPerfomance, MarketStatus
from app.service.watchlist_service import WatchlistService

MAJOR_INDEXES = ["SPY", "QQQ", "DIA"]


class MarketService:
    def __init__(
        self,
        alphavantage_client: AlphaVantageClient,
        watchlist_service: WatchlistService,
    ) -> None:
        self.alphavantage_client = alphavantage_client
        self.watchlist_service = watchlist_service

    async def get_market_status(self, region: str | None = None):
        markets = await self.alphavantage_client.get_market_status()
        watchlist = await self.watchlist_service.get_items()
        status = {
            MarketStatus.OPEN: [],
            MarketStatus.CLOSED: [],
        }
        major_index_performances = []

        for symbol in MAJOR_INDEXES:
            stock_symbol_info = await self.alphavantage_client.get_symbol_info(symbol)
            if len(stock_symbol_info) < 2 or stock_symbol_info[1].close == 0:
                percentage_change = 0
            else:
                change = stock_symbol_info[0].close - stock_symbol_info[1].close
                percentage_change = (change / stock_symbol_info[1].close) * 100

            major_index_performances.append(
                IndexPerfomance(symbol=symbol, percentage_change=percentage_change)
            )

        for market in markets:
            if market.region != region:
                pass

            if market.current_status == MarketStatus.OPEN:
                status[MarketStatus.OPEN] = market
            else:
                status[MarketStatus.CLOSED] = market

        response = {
            "major_index_performances": major_index_performances,
            "status": status,
        }

        if len(watchlist) > 0:
            gainers = []
            losers = []
            perc_changes: list[float] = []

            for item in watchlist:
                stock_symbol_info = await self.alphavantage_client.get_symbol_info(
                    item.symbol
                )

                if stock_symbol_info[1].close == 0:
                    perc_change = 0
                else:
                    change = stock_symbol_info[0].close - stock_symbol_info[1].close
                    perc_change = (change / stock_symbol_info[1].close) * 100
                perc_changes.append(perc_change)

                perc_changes.sort(reverse=True)
                for change in perc_changes:
                    if change > 0:
                        gainers.append(change)

                for change in reversed(perc_changes):
                    if change < 0:
                        losers.append(change)

            response["watchlist"] = {
                "gainers": gainers,
                "losers": losers,
            }

        return response
