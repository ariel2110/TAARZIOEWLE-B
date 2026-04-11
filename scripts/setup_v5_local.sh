#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv || true
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python -m app.db.seed
printf "
Run backend with: uvicorn app.main:app --reload
"
printf "Run frontend-admin with: cd ../frontend-admin && npm install && npm run dev
"
printf "Run frontend-customer with: cd ../frontend-customer && npm install && npm run dev
"
