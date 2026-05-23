def get_ema(
    series_prices: list[float],
    time_period: int,
):
    multiplier = 2 / (time_period + 1)
    seed_data = series_prices[-time_period:]
    previous_ema = sum(seed_data) / time_period

    for price in reversed(series_prices[:-time_period]):
        mva = (price - previous_ema) * multiplier + previous_ema
        previous_ema = mva

    return previous_ema


def get_rsi(
    series_prices: list[float],
    time_period: int = 14,
):
    gains = []
    losses = []

    for i in range(len(series_prices) - 1):
        diff = series_prices[i] - series_prices[i + 1]
        gains.append(max(0, diff))
        losses.append(max(0, -diff))

    avg_gains = sum(gains[:time_period]) / time_period
    avg_losses = sum(losses[:time_period]) / time_period

    for i in range(time_period, len(gains)):
        avg_gains = (avg_gains * (time_period - 1) + gains[i]) / time_period
        avg_losses = (avg_losses * (time_period - 1) + losses[i]) / time_period

    if avg_losses == 0:
        avg_losses = 100

    rs = avg_gains / avg_losses
    return 100 - (100 / (1 + rs))


def get_sma(
    series_prices: list[float],
    time_period: int,
):
    return sum(series_prices[:time_period]) / time_period


INDICATORS: dict[str, callable] = {
    "EMA": get_ema,
    "RSI": get_rsi,
    "SMA": get_sma,
}
