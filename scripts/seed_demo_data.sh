#!/usr/bin/env bash
set -e
cd backend
source .venv/bin/activate 2>/dev/null || true
python -m app.db.seed
