# Financial REST API

Stock market REST API powered by [Alpha Vantage](https://www.alphavantage.co/). Fetch prices and history, compute technical indicators (EMA, SMA, RSI), scan multiple symbols with filters, maintain a watchlist, and read global market status with major index performance.

**Interactive docs:** `/docs` on any running instance (Swagger UI).

---

## Features

- Latest price and OHLCV history for any symbol
- Technical indicators on configurable intervals and series types
- Multi-symbol scan with AND-combined filters
- Personal watchlist with gainers/losers on the market summary
- Market status by region (hours, exchanges, open/closed)
- Response caching and per-client rate limiting

---

## Behavior

These affect how you use the API:

| Topic | Detail |
|-------|--------|
| **Rate limit** | 4 HTTP requests per minute per client IP by default (`429` when exceeded). Protects abuse; configurable via env on the server. |
| **Caching** | Successful Alpha Vantage responses are cached (default **24 hours** for symbol data). Data is **daily OHLCV** (latest bar is typically the previous trading day), not live intraday quotes. Repeated identical upstream queries return cached data. |
| **Watchlist** | Stored per client IP — no login. Your list is tied to the IP the server sees (behind a proxy, that is usually your public IP). |
| **Upstream limits** | Alpha Vantage free tier is ~**5 calls/minute** and ~**25/day** per API key. The server enforces a global upstream budget (**4/min**, **24/day** by default, cache misses only) and returns `503` when exhausted. |
| **Scan / watchlist caps** | **3 symbols** max per scan request and **3 symbols** max per watchlist by default (configurable). |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome / health |
| GET | `/stocks/{symbol}` | Latest close. Query: `time_series` = `DAILY` \| `WEEKLY` \| `MONTHLY` |
| GET | `/stocks/{symbol}/history` | OHLCV bars. Query: `start_date`, `end_date` (`YYYY-MM-DD`) |
| POST | `/stocks/{symbol}/indicators` | EMA, SMA, RSI for a symbol |
| POST | `/stocks/scan` | Evaluate many symbols with optional filters |
| GET | `/watchlist/` | List your watchlist with current prices |
| POST | `/watchlist/{symbol}` | Add a symbol |
| DELETE | `/watchlist/{symbol}` | Remove a symbol |
| GET | `/market/status` | Market hours, SPY/QQQ/DIA performance, watchlist movers. Query: optional `region` |

**Scan filters** — each filter is `{ "type": "<name>", "value": <number> | null }`. All listed filters must pass (AND). Empty `filters` includes every symbol.

| Filter | `value` required | Description |
|--------|------------------|-------------|
| `above_ema_20` | No | Latest close above 20-period EMA |
| `above_sma_50` | No | Latest close above 50-period SMA |
| `ema_crossover` | No | 12-period EMA above 26-period EMA |
| `price_min` | Yes | Close ≥ `value` |
| `price_max` | Yes | Close ≤ `value` |
| `volume_min` | Yes | Volume ≥ `value` |
| `perc_change_min` | Yes | Absolute % change vs prior bar ≥ `value` |
| `perc_change_max` | Yes | Absolute % change vs prior bar ≤ `value` |

Threshold filters with a missing or null `value` never match.

**Status codes:** `400` invalid dates or scan/watchlist limits · `404` not found · `409` symbol already on watchlist · `429` rate limit · `503` upstream error or rate limit

---

## Examples

Replace the base URL with your deployment (e.g. `https://api.yourdomain.com` or `http://127.0.0.1:8000` locally).

```bash
BASE=https://api.yourdomain.com

# Latest price
curl "$BASE/stocks/IBM"

# History
curl "$BASE/stocks/IBM/history?start_date=2026-01-01&end_date=2026-05-01"

# Indicators
curl -X POST "$BASE/stocks/IBM/indicators" \
  -H "Content-Type: application/json" \
  -d '{"indicators":[{"type":"RSI","time_period":14}]}'

# Scan (built-in filter + threshold filter)
curl -X POST "$BASE/stocks/scan" \
  -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL","MSFT"],"indicators":[{"type":"RSI","time_period":14}],"filters":[{"type":"above_ema_20"},{"type":"price_min","value":100}]}'

# Watchlist
curl -X POST "$BASE/watchlist/AAPL"
curl "$BASE/watchlist/"

# Market summary
curl "$BASE/market/status?region=United%20States"
```

Full request/response schemas: **`/docs`**.

---

## Development

To run the project locally, see [docs/SETUP.md](docs/SETUP.md).
