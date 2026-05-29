#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

git fetch origin main
git checkout main
git pull --ff-only origin main

docker compose --profile prod up -d --build
docker compose --profile prod ps
