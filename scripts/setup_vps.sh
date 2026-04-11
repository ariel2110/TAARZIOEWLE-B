#!/usr/bin/env bash
set -e
echo "[setup] Create Python venv, install backend deps, and prepare local DB"
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db.init_db
python -m app.db.seed
echo "[done] Backend starter ready"
