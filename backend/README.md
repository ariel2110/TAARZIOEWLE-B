# Backend — v7

This backend is now closer to a real project foundation.

## Highlights
- PostgreSQL-first config path
- Alembic wiring improved
- initial real migration file included
- JWT auth skeleton with `/api/v1/auth/dev-login`
- Docker-friendly

## Recommended local run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.db.seed_cli
uvicorn app.main:app --reload
```


## V8 Notes
- queue summary endpoints added
- approval actions now create activity logs
- CEO digest returns richer operational counts
