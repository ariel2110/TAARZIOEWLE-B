#!/usr/bin/env bash
# deploy.sh — Full production deploy for SiteNest platform
# Usage: bash scripts/deploy.sh [--no-build]
set -euo pipefail

SKIP_BUILD="${1:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[deploy] SiteNest deployment started — $(date)"

# ── 1. Pull latest code ────────────────────────────────────────────
echo "[deploy] Pulling latest from git..."
git -C "$ROOT" pull --ff-only

# ── 2. Backend: install deps + migrate ────────────────────────────
echo "[deploy] Installing backend dependencies..."
cd "$ROOT/backend"
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt --quiet

echo "[deploy] Running Alembic migrations..."
alembic upgrade head

echo "[deploy] Backend migrations done."

# ── 3. Build frontends ─────────────────────────────────────────────
if [[ "$SKIP_BUILD" != "--no-build" ]]; then
  echo "[deploy] Building admin frontend..."
  cd "$ROOT/frontend-admin"
  npm ci --silent
  npm run build

  echo "[deploy] Building customer frontend..."
  cd "$ROOT/frontend-customer"
  npm ci --silent
  npm run build

  echo "[deploy] Building public frontend..."
  cd "$ROOT/frontend-public"
  npm ci --silent
  npm run build 2>/dev/null || true
fi

# ── 4. Restart services ────────────────────────────────────────────
echo "[deploy] Restarting backend service..."
sudo systemctl restart localbiz-backend 2>/dev/null || echo "[warn] systemctl not available — restart manually"

echo "[deploy] Done! — $(date)"
