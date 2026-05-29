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

- Python 3.12+ (local development)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (production-style local runs and EC2)
- Alpha Vantage API key ([free tier](https://www.alphavantage.co/support/#api-key))

## Project structure

```
src/app/
├── api/              # Route handlers (stocks, watchlist, market)
├── clients/          # Alpha Vantage & Redis clients
├── core/             # Config, logging
├── domain/           # Pure indicator / filter / metric logic
├── middleware/       # Rate limiting
├── schemas/          # Pydantic models
└── services/         # Business logic
```

## Configuration

Copy the example env file and add your secrets (`.env` is gitignored):

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `ALPHA_VANTAGE_API_KEY` | Required for live market data |
| `ALPHA_VANTAGE_BASE_URL` | Usually `https://www.alphavantage.co/query` |
| `REDIS_URL` | Redis hostname (see below) |
| `REDIS_PORT` | Redis port (usually `6379`) |
| `REDIS_USERNAME` / `REDIS_PASSWORD` | Optional; leave empty for local Redis |
| `TTL` | Cache TTL in seconds for successful AV responses (default `60`) |

**Where Redis points depends on how you run the API:**

| How you run | `REDIS_URL` | Notes |
|-------------|-------------|--------|
| API on host (`fastapi dev`) | `localhost` | Use `.env.local` for local overrides (loaded after `.env`) |
| `docker compose up` | `redis` | Set automatically in `docker-compose.yml` (Compose service name) |
| EC2 with Compose | `redis` | Same as compose; do **not** use `localhost` inside the API container |

`src/app/core/config.py` loads `.env` then `.env.local` (override) from the repo root.

## Local development (API on host)

### 1. Install dependencies

From the repository root:

```bash
uv sync
```

### 2. Start Redis

Use **one** Redis instance for both the API and `redis-cli`. On macOS, Homebrew Redis and Docker often both bind port **6379**; the API uses `localhost` and usually hits **brew Redis**, while `docker exec … redis-cli` talks to the **container** (a separate database).

**Homebrew / local Redis only**

```bash
brew services start redis
redis-cli KEYS '*'
```

**Docker Redis only** (stop brew first)

```bash
brew services stop redis
docker run -d --name redis -p 6379:6379 redis:alpine
docker exec -it redis redis-cli KEYS '*'
```

**Docker on host port 6380** (keep brew on 6379)

```bash
docker run -d --name redis -p 6380:6379 redis:alpine
# in .env.local: REDIS_PORT=6380
```

Verify you are on the same Redis as the app:

```bash
lsof -i :6379
redis-cli -h 127.0.0.1 -p 6379 DBSIZE
docker exec redis redis-cli DBSIZE   # should match if only Docker uses 6379
```

### 3. Run the API

From the `src` directory:

```bash
cd src
uv run fastapi dev app/main.py --reload
```

Docs: **http://127.0.0.1:8000/docs**

### 4. Run tests

From the repository root:

```bash
uv run pytest
```

## Docker Compose (API + Redis)

Runs the API and Redis as two containers on one host (local prod-like setup or EC2).

```bash
cp .env.example .env   # add ALPHA_VANTAGE_API_KEY at minimum
docker compose up --build
```

- API: **http://127.0.0.1:8000**
- Compose sets `REDIS_URL=redis` and `REDIS_PORT=6379` for the API container (overrides `.env` for Redis host).
- Redis data is persisted in the named volume `redis_data` mounted at `/data` inside the Redis container (survives `docker compose restart`; removed with `docker compose down -v`).

Inspect cache keys (from the host):

```bash
docker compose exec redis redis-cli KEYS 'cache:*'
docker compose exec redis redis-cli TTL 'cache:api-requests:...'
```

Remember cached keys expire after `TTL` seconds (default 60).

## Deploying to AWS EC2 (Option B)

Self-hosted Redis on the same instance as the API via Docker Compose (no Redis Cloud required in production).

1. Launch an EC2 instance (e.g. Ubuntu 22.04) with security group rules for SSH (`22`) and HTTP (`8000`, or `80`/`443` if you add a reverse proxy).
2. Install Docker and the Compose plugin on the instance.
3. Clone the repo and create `.env` on the server with at least `ALPHA_VANTAGE_API_KEY` (and other vars from `.env.example`).
4. From the repo root on EC2:

   ```bash
   docker compose up -d --build
   ```

5. Open `http://<ec2-public-ip>:8000/docs` to verify.

Compose wires the API to Redis using the hostname `redis` on the internal Docker network. You do not need Cloud Redis URLs in production `.env` unless you choose a managed Redis service later.

**Optional hardening:** put Nginx or Caddy in front of the API on 443, restrict Redis so port `6379` is not exposed publicly (the default compose file does not publish Redis to the host), and use IAM/instance roles or Secrets Manager for env secrets instead of committing `.env`.

### Automated deployment (GitHub Actions)

After tests pass on a **push to `main`**, the [Deploy workflow](.github/workflows/deploy.yml) SSHs into EC2 and runs [`scripts/deploy.sh`](scripts/deploy.sh) (`git pull` + `docker compose up -d --build`).

#### One-time EC2 setup for `git pull`

The instance must pull from GitHub without a password prompt. Use a **read-only deploy key**:

```bash
# On EC2
ssh-keygen -t ed25519 -C "ec2-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub
```

In GitHub: **Repo → Settings → Deploy keys → Add deploy key** (read-only). Paste the public key.

```bash
# On EC2 — use the deploy key for GitHub
cat >> ~/.ssh/config <<'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_deploy
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config ~/.ssh/github_deploy

# Clone with SSH (if not already cloned)
git clone git@github.com:<your-username>/financial-rest-api.git ~/financial-rest-api
cd ~/financial-rest-api
cp .env.example .env && nano .env   # production secrets, once
docker compose up -d --build
```

#### GitHub repository secrets

**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|--------|--------|
| `EC2_HOST` | Public IP or Elastic IP (e.g. `34.200.251.106`) |
| `EC2_USER` | `ubuntu` (Ubuntu AMI) |
| `EC2_SSH_KEY` | Full contents of your `.pem` private key |
| `EC2_APP_PATH` | Optional; default `~/financial-rest-api` |

#### Security group note

GitHub-hosted runners use **dynamic IP addresses**. For SSH deploy to work, port **22** must be reachable from the runner. Options:

- **Portfolio / demo:** allow SSH from `0.0.0.0/0` (weaker; prefer a dedicated deploy user and key rotation).
- **Tighter:** use a [self-hosted runner](https://docs.github.com/en/actions/hosting-your-own-runners) on EC2, or AWS SSM instead of SSH.

#### Flow

```
push to main → CI (pytest) → Deploy workflow → SSH → scripts/deploy.sh
```

Manual deploy on the server (same as the script):

```bash
bash ~/financial-rest-api/scripts/deploy.sh
```

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

- [x] Docker / docker-compose
- [x] AWS EC2 deployment (see [Deploying to AWS EC2](#deploying-to-aws-ec2-option-b))
- [x] CI deploy to EC2 on push to `main` (see [Automated deployment](#automated-deployment-github-actions))
- [ ] Scan filter thresholds in request body
- [ ] Optional authentication beyond client IP
- [ ] HTTPS reverse proxy and Elastic IP

## License

Private / portfolio project — add a license if you open-source it.
