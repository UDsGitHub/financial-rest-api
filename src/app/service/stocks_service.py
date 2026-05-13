from app.clients.alpha_vantage_client import AlphaVantageClient

class StocksService:
    def __init__(self, alphavantage_client: AlphaVantageClient) -> None:
        self.alphavantage_client = alphavantage_client

    async def get_stock_price(self, symbol: str, time_series: str) -> float:
        stock_symbol_info = await self.alphavantage_client.get_symbol_info(symbol, time_series)
        return stock_symbol_info[0].close
    
    async def get_stock_indicators(self, symbol: str) -> list:
        return []

    async def get_stock_history(self, start_date: str, end_date: str) -> list:
        return []