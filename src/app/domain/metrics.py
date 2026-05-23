from app.schemas.stocks import OHLCV

def day_over_day_percent_change(bars: list[OHLCV]) -> float:
    if len(bars) < 2 or bars[1].close == 0:
        return 0.0
    change = bars[0].close - bars[1].close
    return (change / bars[1].close) * 100