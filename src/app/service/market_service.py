from clients.alpha_vantage_client import AlphaVantageClient

class MarketService:
    def __init__(self, alphavantage_client: AlphaVantageClient) -> None:
        self.alphavantage_client = alphavantage_client

    async def get_market_summary(self):
        return None