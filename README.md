# Financial REST API

A Python REST API built with **FastAPI** that aggregates stock market data from [Alpha Vantage](https://www.alphavantage.co/), computes technical indicators, and exposes watchlist and market-summary endpoints. Responses are cached in **Redis** to reduce upstream API usage.

Interactive API docs: **http://127.0.0.1:8000/docs** (when running locally).

## Features

- Stock price, history, and technical indicators (EMA, SMA, RSI)
- Market status by region with major index performance (SPY, QQQ, DIA)
- Per-client watchlist (keyed by request IP) with gainers/losers on market summary
- Multi-symbol scan with optional filters
- Global Redis cache for Alpha Vantage responses (configurable TTL)
- Per-IP rate limiting (25 requests / 60 seconds) with in-memory fallback if Redis is unavailable

## Tech stack

- **FastAPI** — HTTP API
- **Alpha Vantage** — market data
- **Redis** — response cache, watchlist storage, rate-limit counters
- **httpx** — async HTTP client
- **Pydantic** — request/response models

## Prerequisites

- Python 3.12+
- Redis (local or remote)
- Alpha Vantage API key ([free tier](https://www.alphavantage.co/support/#api-key))

## Project structure

```
src/app/
├── api/              # Route handlers (stocks, watchlist, market)
├── clients/          # Alpha Vantage & Redis clients
├── core/             # Config, logging
├── middleware/       # Rate limiting
├── schemas/          # Pydantic models
└── service/          # Business logic
```

## Setup

### 1. Install dependencies

From the repository root (uses [uv](https://github.com/astral-sh/uv) or pip):

```bash
uv sync
# or: pip install -e .
```

### 2. Configure environment

Copy the example env file and add your secrets (`.env` is gitignored):

```bash
cp .env.example .env
```

Edit `.env` and set at least `ALPHA_VANTAGE_API_KEY`. See `.env.example` for all variables.

### 3. Start Redis

```bash
redis-server
# or: docker run -d -p 6379:6379 redis:alpine
```

### 4. Run the API

From the `src` directory:

```bash
cd src
fastapi dev app/main.py --reload
```

The server listens on **http://127.0.0.1:8000** by default.

## Rate limiting

- **25 requests per minute** per client IP (`request.client.host`)
- Over limit: `429` with `{"detail": "Rate limit exceeded"}`
- If Redis is down, limits fall back to an in-process store (per server process)

## Caching

Successful Alpha Vantage responses are stored under global keys such as:

`cache:api-requests:{url-with-function-and-symbol}`

- Default TTL: **60 seconds** (`TTL` env var)
- Error/rate-limit payloads are **not** cached
- If Redis read fails, the app still calls Alpha Vantage directly

Alpha Vantage free tier allows about **5 calls/minute** — caching and scan discipline matter for demos.

## Watchlist behavior

Watchlists are scoped by **client IP** (no auth). Suitable for local demos; not for multi-tenant production without real authentication.

| Method | Path | Response |
|--------|------|----------|
| GET | `/watchlist/` | List of `{ symbol, price, date }` (prices refreshed from Alpha Vantage) |
| POST | `/watchlist/{symbol}` | Single added `{ symbol, price, date }` |
| DELETE | `/watchlist/{symbol}` | Removed `symbol` string |

## API reference

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome message |

### Stocks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/stocks/{symbol}` | Latest close price |
| GET | `/stocks/{symbol}/history` | OHLCV bars in date range |
| POST | `/stocks/{symbol}/indicators` | Computed indicators |
| POST | `/stocks/scan` | Scan symbols with filters |

**GET `/stocks/{symbol}`**

Query parameters:

| Param | Default | Values |
|-------|---------|--------|
| `time_series` | `DAILY` | `DAILY`, `WEEKLY`, `MONTHLY` |

Response: `float` (latest close).

**GET `/stocks/{symbol}/history`**

Query parameters:

| Param | Format | Example |
|-------|--------|---------|
| `start_date` | `YYYY-MM-DD` | `2026-01-01` |
| `end_date` | `YYYY-MM-DD` | `2026-05-01` |

Response: array of OHLCV objects (`open`, `high`, `low`, `close`, `volume`, `date`).

**POST `/stocks/{symbol}/indicators`**

Request body:

```json
{
  "indicators": [
    { "type": "EMA", "time_period": 20 },
    { "type": "RSI", "time_period": 14 }
  ],
  "interval": "DAILY",
  "series_type": "close"
}
```

| Field | Notes |
|-------|--------|
| `indicators[].type` | `EMA`, `SMA`, or `RSI` |
| `indicators[].time_period` | Lookback period (required for EMA/SMA) |
| `interval` | `DAILY`, `WEEKLY`, or `MONTHLY` |
| `series_type` | `open`, `high`, `low`, `close`, or `volume` |

**POST `/stocks/scan`**

Request body:

```json
{
  "symbols": ["AAPL", "MSFT", "IBM"],
  "indicators": [{ "type": "RSI", "time_period": 14 }],
  "filters": ["above_ema_20", "ema_crossover"]
}
```

| Field | Behavior |
|-------|----------|
| `symbols` | Symbols to evaluate |
| `indicators` | Computed only for symbols that pass all filters (or all symbols if `filters` is empty) |
| `filters` | All listed filters must pass (AND). Empty list = every symbol included |

**Scan filters**

| Filter | Description |
|--------|-------------|
| `above_ema_20` | Latest close above 20-period EMA |
| `above_sma_50` | Latest close above 50-period SMA |
| `ema_crossover` | 12-period EMA above 26-period EMA |
| `price_min` | Close ≥ threshold (threshold not exposed via API yet) |
| `price_max` | Close ≤ threshold (threshold not exposed via API yet) |
| `volume_min` | Volume ≥ threshold (threshold not exposed via API yet) |
| `perc_change_min` | Absolute % change vs prior bar ≥ threshold |
| `perc_change_max` | Absolute % change vs prior bar ≤ threshold |

Response:

```json
{
  "timestamp": "2026-05-20T12:00:00Z",
  "results": [
    {
      "symbol": "AAPL",
      "indicators": [{ "RSI_14": 55.2 }],
      "matched_filters": ["above_ema_20"]
    }
  ],
  "total_scanned": 3,
  "total_matched": 1
}
```

### Market

| Method | Path | Description |
|--------|------|-------------|
| GET | `/market/status` | Market hours, index performance, watchlist gainers/losers |

Query parameters:

| Param | Description |
|-------|-------------|
| `region` | Optional; filter markets (e.g. `United States`). Omit for all regions. |

Response includes:

- `major_index_performances` — day-over-day % change for SPY, QQQ, DIA
- `status` — markets grouped by region, split into `open` / `closed`
- `watchlist` (if non-empty) — `gainers` and `losers` with `{ symbol, change }` (percent string)

## Example requests

```bash
# Latest price
curl "http://127.0.0.1:8000/stocks/IBM"

# History
curl "http://127.0.0.1:8000/stocks/IBM/history?start_date=2026-01-01&end_date=2026-05-01"

# Indicators
curl -X POST "http://127.0.0.1:8000/stocks/IBM/indicators" \
  -H "Content-Type: application/json" \
  -d '{"indicators":[{"type":"RSI","time_period":14}]}'

# Add to watchlist
curl -X POST "http://127.0.0.1:8000/watchlist/AAPL"

# Market summary (uses your watchlist for gainers/losers)
curl "http://127.0.0.1:8000/market/status"
curl "http://127.0.0.1:8000/market/status?region=United%20States"
```

## HTTP status codes

| Code | When |
|------|------|
| `400` | Invalid date format or range on history |
| `404` | Symbol/series not found |
| `409` | Symbol already on watchlist |
| `429` | App rate limit exceeded |
| `503` | Alpha Vantage error or rate limit (`Information` / `Error Message` in upstream JSON) |

## Roadmap

- [ ] Docker / docker-compose
- [ ] AWS EC2 deployment
- [ ] Scan filter thresholds in request body
- [ ] Optional authentication beyond client IP

## License

Private / portfolio project — add a license if you open-source it.
