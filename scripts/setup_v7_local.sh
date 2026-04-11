#!/usr/bin/env bash
set -e

echo '[v7] Copy backend/.env.example to backend/.env and adjust if needed.'
echo '[v7] Start postgres via docker compose or local service.'
echo '[v7] Then run:'
echo '  cd backend && python -m venv .venv && source .venv/bin/activate'
echo '  pip install -r requirements.txt'
echo '  alembic upgrade head'
echo '  python -m app.db.seed_cli'
echo '  uvicorn app.main:app --reload'
