from fastapi import HTTPException, status
import httpx
from app.config import config
from app.schemas.stocks import OHLCV, TimeSeries

BASE_URL = config.ALPHA_VANTAGE_BASE_URL
API_KEY = config.ALPHA_VANTAGE_API_KEY


class AlphaVantageClient:
    async def get_symbol_info(
        self, symbol: str, time_series: str = "DAILY"
    ) -> list[OHLCV] | None:
        match time_series:
            case TimeSeries.DAILY:
                time_series_function = TimeSeries.value_map[TimeSeries.DAILY]
            case TimeSeries.WEEKLY:
                time_series_function = TimeSeries.value_map[TimeSeries.WEEKLY]
            case TimeSeries.MONTHLY:
                time_series_function = TimeSeries.value_map[TimeSeries.MONTHLY]
            case _:
                time_series_function = TimeSeries.value_map[TimeSeries.DAILY]

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
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Error fetching symbol details')

            time_series_key = f"Time Series ({time_series.title()})"
            time_series_items = response_json[time_series_key].items()
            time_series_values: list[OHLCV] = []

            if len(time_series_items) == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Symbol price info not found')

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
