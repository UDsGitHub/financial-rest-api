from fastapi import HTTPException, status
import httpx
from app.config import config
from app.schemas.stocks import OHLCV, TimeInterval
from app.schemas.market import Market

BASE_URL = config.ALPHA_VANTAGE_BASE_URL
API_KEY = config.ALPHA_VANTAGE_API_KEY


class AlphaVantageClient:
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

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}",
                params={
                    "function": time_series_function,
                    "symbol": symbol,
                    "apikey": API_KEY,
                },
            )
            response_json = response.json()

            if "Error Message" in response_json or "Information" in response_json:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error fetching symbol details",
                )

            time_series_key = f"Time Series ({time_interval.title()})"
            time_series_items = response_json[time_series_key].items()
            time_series_values: list[OHLCV] = []

            if len(time_series_items) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Symbol price info not found",
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
    
    
    async def get_market_status(
        self
    ) -> list[Market] | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}",
                params={
                    "function": 'MARKET_STATUS',
                    "apikey": API_KEY,
                },
            )
            response_json = response.json()

            if "Error Message" in response_json or "Information" in response_json or markets not in response_json or len(response_json['markets']) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error fetching market summary",
                )

            markets = response_json['markets']
            response: list[Market] = []
            for val in markets:
                primary_exchanges = val['primary_exchanges'].split(', ')
                market_val = Market(
                    market_type=val['market_type'],
                    region=val['region'],
                    primary_exchanges=primary_exchanges,
                    local_open=val['local_open'],
                    local_close=val['local_close'],
                    current_status=val['current_status'],
                    notes=val['notes'],
                )
                response.append(market_val)

            return response
