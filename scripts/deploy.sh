#!/usr/bin/env bash
# deploy.sh — Full production deploy for TAZO-WEB platform
# Usage:  bash scripts/deploy.sh [--no-build]
# Remote: ssh root@76.13.48.23 "cd /root/TAARZIOEWLE-B && bash scripts/deploy.sh"
set -euo pipefail

SKIP_BUILD="${1:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT/docker-compose.yml"

echo "[deploy] ★ TAZO-WEB deployment started — $(date)"

# ── 1. Pull latest code ────────────────────────────────────────────
echo "[deploy] Pulling latest from git..."
git -C "$ROOT" pull --ff-only

# ── 2. Build frontends (inside Docker or locally if npm available) ─
if [[ "$SKIP_BUILD" != "--no-build" ]]; then
  for app in frontend-admin frontend-customer frontend-public; do
    if [ -d "$ROOT/$app" ]; then
      echo "[deploy] Building $app..."
      cd "$ROOT/$app"
      npm ci --silent
      npm run build
    fi
  done
  cd "$ROOT"
fi

# ── 3. Rebuild & restart Docker services ──────────────────────────
echo "[deploy] Rebuilding backend image..."
docker compose -f "$COMPOSE_FILE" build --no-cache backend

echo "[deploy] Restarting all services..."
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

# ── 4. Run DB migrations ───────────────────────────────────────────
echo "[deploy] Waiting for DB to be ready..."
sleep 5
echo "[deploy] Running Alembic migrations..."
docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head || \
  echo "[warn] Migration failed or already up-to-date"

echo "[deploy] ✅ TAZO-WEB deployment complete — $(date)"
echo "[deploy] Services status:"
docker compose -f "$COMPOSE_FILE" ps

