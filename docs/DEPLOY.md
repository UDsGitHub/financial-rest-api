# EC2 deployment (personal reference)

Option B: API + Redis + Caddy on one EC2 instance. Compose profile `prod` enables HTTPS via Let's Encrypt.

## Architecture

```
Internet → :443/:80 Caddy → api:8000 (internal) → redis (internal)
```

- API is not published on host port 8000 in production (only `expose` on Docker network).
- Redis is never exposed publicly.
- Caddy certs live in Docker volume `caddy_data`; Redis data in `redis_data`.

## AWS one-time setup

### EC2 instance

- Ubuntu 22.04/24.04, e.g. `t3.micro`
- Install Docker + Compose plugin
- Security group inbound:

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | `0.0.0.0/0` (or GitHub runner IPs) | SSH + CI deploy |
| 80 | TCP | `0.0.0.0/0` | HTTP (ACME challenge + redirect) |
| 443 | TCP | `0.0.0.0/0` | HTTPS API |

### Elastic IP

1. EC2 → Elastic IPs → Allocate
2. Associate with the instance
3. Use this IP for DNS and GitHub secret `EC2_HOST`

Stop/start without Elastic IP changes the public IP and breaks DNS.

### DNS

A record: `api.yourdomain.com` → Elastic IP. HTTPS will not issue until DNS resolves to the server.

## Server setup

### Deploy key (for `git pull` without password)

```bash
ssh-keygen -t ed25519 -C "ec2-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub
```

GitHub → Repo → Settings → Deploy keys → Add (read-only).

```bash
cat >> ~/.ssh/config <<'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_deploy
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config ~/.ssh/github_deploy
```

### Clone and env

```bash
git clone git@github.com:<username>/financial-rest-api.git ~/financial-rest-api
cd ~/financial-rest-api
cp .env.example .env
nano .env
```

Production `.env` minimum:

```env
ALPHA_VANTAGE_API_KEY=...
DOMAIN=api.yourdomain.com
ACME_EMAIL=you@example.com
# Optional — defaults in config.py if omitted:
# CACHE_TTL=86400
# RATE_LIMIT_WINDOW=60
# MAX_REQUESTS_PER_MINUTE=4
```

Compose overrides Redis to `REDIS_URL=redis` / `REDIS_PORT=6379` for the API container. Cloud Redis not required on EC2.

### Start / restart

```bash
docker compose --profile prod up -d --build
```

Manual deploy (same as CI script):

```bash
bash ~/financial-rest-api/scripts/deploy.sh
```

## Caddy

`Caddyfile` at repo root:

- Global block: `email {$ACME_EMAIL}` for Let's Encrypt account contact (not app login).
- Site block: `{$DOMAIN}` → `reverse_proxy api:8000`.

Env vars `DOMAIN` and `ACME_EMAIL` are passed into the Caddy container from `.env`.

`main.py` uses `ProxyHeadersMiddleware` so rate limits and watchlist see the real client IP behind Caddy.

## GitHub Actions CI/CD

**CI** (`.github/workflows/ci.yml`): pytest on push/PR to `main`.

**Deploy** (`.github/workflows/deploy.yml`): after CI succeeds on push to `main`, SSH to EC2 and run `scripts/deploy.sh`.

### Repository secrets

| Secret | Value |
|--------|--------|
| `EC2_HOST` | Elastic IP |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Full `.pem` private key contents |
| `EC2_APP_PATH` | Optional; defaults to `~/financial-rest-api` |

GitHub-hosted runners use dynamic IPs — SSH (22) must be reachable from the runner (common demo fix: allow `0.0.0.0/0` on 22). Tighter options: self-hosted runner on EC2 or AWS SSM.

### Flow

```
push to main → CI (pytest) → Deploy workflow → SSH → scripts/deploy.sh → git pull + compose --profile prod
```

## Useful commands on EC2

```bash
docker compose --profile prod ps
docker compose --profile prod logs -f api
docker compose --profile prod logs -f caddy
docker compose exec redis redis-cli KEYS 'cache:*'
docker compose --profile prod down      # stop
docker compose --profile prod down -v   # stop + delete volumes (Redis + certs)
```

## Troubleshooting notes

| Issue | Likely cause |
|-------|----------------|
| Deploy SSH `i/o timeout` | Security group blocks port 22 from GitHub runners |
| HTTPS cert fails | DNS not pointing at Elastic IP, or port 80 blocked |
| Empty Redis keys in `docker exec` | Wrong Redis instance (macOS brew vs Docker both on 6379) |
| `503` on stock endpoints | Alpha Vantage rate limit or bad API key in server `.env` |
