from app.clients.alpha_vantage_client import AlphaVantageClient
from app.data.data import MAJOR_INDEXES
from app.schemas.market import IndexPerfomance, MarketStatus
from app.services.watchlist.watchlist_service import WatchlistService
from app.services.market.market_service_interface import IMarketService
from app.domain.metrics import day_over_day_percent_change


class MarketService(IMarketService):
    def __init__(
        self,
        alphavantage_client: AlphaVantageClient,
        watchlist_service: WatchlistService,
    ) -> None:
        self.alphavantage_client = alphavantage_client
        self.watchlist_service = watchlist_service

    async def get_market_status(self, ip: str, region: str | None = None):
        markets = await self.alphavantage_client.get_market_status()
        watchlist_symbols = await self.watchlist_service.get_symbols(ip)
        status = {}
        major_index_performances = []

        for symbol in MAJOR_INDEXES:
            stock_symbol_info = await self.alphavantage_client.get_symbol_info(symbol)
            percentage_change = day_over_day_percent_change(stock_symbol_info)
            major_index_performances.append(
                IndexPerfomance(symbol=symbol, percentage_change=percentage_change)
            )

        for market in markets:
            if region is not None and market.region != region:
                continue

            if market.region not in status:
                status[market.region] = {
                    MarketStatus.OPEN.name: [],
                    MarketStatus.CLOSED.name: [],
                }

            if market.current_status == MarketStatus.OPEN.name:
                status[market.region][MarketStatus.OPEN.name].append(market)
            else:
                status[market.region][MarketStatus.CLOSED.name].append(market)

        response = {
            "major_index_performances": major_index_performances,
            "status": status,
        }

        if len(watchlist_symbols) > 0:
            gainers = []
            losers = []
            perc_changes: list[tuple[str, float]] = []

            for symbol in watchlist_symbols:
                stock_symbol_info = await self.alphavantage_client.get_symbol_info(
                    symbol
                )

                perc_change = day_over_day_percent_change(stock_symbol_info)
                perc_changes.append((symbol, perc_change))

            perc_changes = sorted(perc_changes, key=lambda x: x[1], reverse=True)
            for change in perc_changes:
                if change[1] > 0:
                    gainers.append({"symbol": change[0], "change": f"{change[1]}%"})

            for change in sorted(perc_changes, key=lambda x: x[1]):
                if change[1] < 0:
                    losers.append({"symbol": change[0], "change": f"{change[1]}%"})

            response["watchlist"] = {
                "gainers": gainers,
                "losers": losers,
            }

        return response
