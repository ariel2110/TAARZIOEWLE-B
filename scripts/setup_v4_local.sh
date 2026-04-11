#!/usr/bin/env bash
set -e
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "from app.db.init_db import init_db; init_db()"
python -c "from app.db.session import SessionLocal; from app.db.seed import seed_demo_data; db=SessionLocal(); seed_demo_data(db); db.close()"
echo 'Local v4 backend is initialized.'
