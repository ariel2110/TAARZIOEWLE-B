#!/usr/bin/env bash
set -e
echo "[setup] Create Python venv, install backend deps, and prepare local DB"
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "[setup] Running Alembic migrations..."
alembic upgrade head
echo "[setup] Seeding demo data..."
python -m app.db.seed 2>/dev/null || true
echo "[done] Backend starter ready"
