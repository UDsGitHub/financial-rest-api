# Local setup

How to run this project on your machine. For API usage and endpoints, see the [main README](../README.md).

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Redis (local or Docker)
- Alpha Vantage API key ([free tier](https://www.alphavantage.co/support/#api-key))

## Configuration

```bash
cp .env.example .env
```

Add your `ALPHA_VANTAGE_API_KEY`. Optional: copy to `.env.local` for overrides (gitignored; loaded after `.env`).

| Variable | Default | Purpose |
|----------|---------|---------|
| `ALPHA_VANTAGE_API_KEY` | — | Required |
| `REDIS_URL` | `localhost` | |
| `REDIS_PORT` | `6379` | Use `6380` if Docker Redis maps host 6380→6379 |
| `CACHE_TTL` | `86400` | Seconds to cache successful AV responses (24h; matches daily bar data) |
| `RATE_LIMIT_WINDOW` | `60` | Rate-limit window in seconds |
| `MAX_REQUESTS_PER_MINUTE` | `4` | Max HTTP requests per IP per window |

For faster cache turnover while developing, set a lower `CACHE_TTL` in `.env.local` (e.g. `300`).

See `.env.example` for all variables. Production-only vars (`DOMAIN`, `ACME_EMAIL`) are not needed locally.

## Run on host (recommended for dev)

```bash
uv sync
cd src && uv run fastapi dev app/main.py --reload
```

API: http://127.0.0.1:8000 · Docs: http://127.0.0.1:8000/docs

## Redis

The API expects Redis on the host/port in your env.

**macOS:** Homebrew Redis and Docker Redis both often use port `6379`. The app connects to `localhost` (usually brew); `docker exec redis-cli` hits the container — a separate database. Pick one:

- Brew only: `brew services start redis`
- Docker only: `brew services stop redis`, then `docker run -d --name redis -p 6379:6379 redis:alpine`
- Both: map Docker to `6380` and set `REDIS_PORT=6380` in `.env.local`

## Docker (local)

Runs API + Redis in containers (no HTTPS):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Compose overrides `REDIS_URL` to `redis` inside the API container.

## Tests

From the repo root:

```bash
uv sync --group dev
uv run pytest
```

## Project layout

```
src/app/
├── api/          # Route handlers
├── clients/      # Alpha Vantage, Redis
├── core/         # Config, logging
├── domain/       # Indicators, filters, metrics
├── middleware/   # Rate limiting
├── schemas/      # Pydantic models
└── services/     # Business logic
```
