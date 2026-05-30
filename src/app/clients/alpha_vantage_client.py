import json
from fastapi import HTTPException, status
import httpx
import redis
from app.clients.av_budget import reserve_upstream_call
from app.core.config import config
from app.schemas.stocks import OHLCV, TimeInterval
from app.schemas.market import Market
from app.clients.redis_client import redis_client
from app.core.logger import logger
from app.schemas.logger import LoggerConstants

BASE_URL = config.ALPHA_VANTAGE_BASE_URL
API_KEY = config.ALPHA_VANTAGE_API_KEY


class AlphaVantageClient:
    def get_cache_key(self):
        return f"cache:api-requests"

    async def _log_api_request(self, key: str, value: str):
        try:
            await redis_client.set(key, value, ex=config.CACHE_TTL)
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)

    async def _fetch_upstream(self, params: dict) -> dict:
        await reserve_upstream_call()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                BASE_URL,
                params={**params, "apikey": API_KEY},
            )
            return response.json()

    async def get_symbol_info(
        self, symbol: str, time_interval: str = "DAILY"
    ) -> list[OHLCV]:
        match time_interval:
            case TimeInterval.DAILY:
                time_series_function = TimeInterval.value_map[TimeInterval.DAILY]
            case TimeInterval.WEEKLY:
                time_series_function = TimeInterval.value_map[TimeInterval.WEEKLY]
            case TimeInterval.MONTHLY:
                time_series_function = TimeInterval.value_map[TimeInterval.MONTHLY]
            case _:
                time_series_function = TimeInterval.value_map[TimeInterval.DAILY]

        cache_key = self.get_cache_key()
        request_path = f"{BASE_URL}?function={time_series_function}&symbol={symbol}"
        composed_key = f"{cache_key}:{request_path}"
        cache_value = None
        response_json = None

        try:
            cache_value = await redis_client.get(composed_key)
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)

        if cache_value is not None:
            response_json = json.loads(cache_value)
        else:
            response_json = await self._fetch_upstream(
                {"function": time_series_function, "symbol": symbol}
            )

        if "Error Message" in response_json or "Information" in response_json:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error fetching symbol details, symbol={symbol}",
            )

        if cache_value is None:
            await self._log_api_request(composed_key, json.dumps(response_json))

        time_series_key = f"Time Series ({time_interval.title()})"
        time_series_items = response_json[time_series_key].items()
        time_series_values: list[OHLCV] = []

        if len(time_series_items) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbol price info not found, symbol={symbol}",
            )

        for key, val in time_series_items:
            ohlcv_value = OHLCV(
                open=val["1. open"],
                high=val["2. high"],
                low=val["3. low"],
                close=val["4. close"],
                volume=val["5. volume"],
                date=key,
            )
            time_series_values.append(ohlcv_value)

        return time_series_values

    async def get_market_status(self) -> list[Market] | None:
        cache_key = self.get_cache_key()
        request_path = f"{BASE_URL}?function=MARKET_STATUS"
        composed_key = f"{cache_key}:{request_path}"
        cache_value = None
        response_json = None

        try:
            cache_value = await redis_client.get(composed_key)
        except redis.ConnectionError:
            logger.warning(LoggerConstants.CACHE_CONN_ERR)

        if cache_value is not None:
            response_json = json.loads(cache_value)
        else:
            response_json = await self._fetch_upstream({"function": "MARKET_STATUS"})

        if (
            "Error Message" in response_json
            or "Information" in response_json
            or "markets" not in response_json
            or len(response_json["markets"]) == 0
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error fetching market summary",
            )

        if cache_value is None:
            await self._log_api_request(composed_key, json.dumps(response_json))

        markets = response_json["markets"]
        response = []
        for val in markets:
            primary_exchanges = val["primary_exchanges"].split(", ")
            market_val = Market(
                market_type=val["market_type"],
                region=val["region"],
                primary_exchanges=primary_exchanges,
                local_open=val["local_open"],
                local_close=val["local_close"],
                current_status=val["current_status"],
                notes=val["notes"],
            )
            response.append(market_val)

        return response
