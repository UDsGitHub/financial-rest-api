import httpx
from app.config import config

BASE_URL = config.ALPHA_VANTAGE_BASE_URL
API_KEY = config.ALPHA_VANTAGE_API_KEY

class AlphaVantageClient:
    async def get_symbol_info(symbol: str):
        async with httpx.AsyncClient as client:
            response = await client.get(
                BASE_URL,
                params={"symbol": symbol}
            )

            return response.json()