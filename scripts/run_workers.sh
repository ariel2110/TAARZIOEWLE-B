#!/usr/bin/env bash
# run_workers.sh — Run all workers once (suitable for cron or manual trigger)
# For continuous scheduling, use the provided systemd timer units or crontab entries.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
source .venv/bin/activate 2>/dev/null || true

echo "[workers] $(date) — Running CEO digest worker..."
python -m app.workers.ceo_digest_worker || echo "[workers] ceo_digest_worker exited with error"

echo "[workers] $(date) — Running follow-up worker..."
python -m app.workers.followup_worker || echo "[workers] followup_worker exited with error"

echo "[workers] All workers done — $(date)"

