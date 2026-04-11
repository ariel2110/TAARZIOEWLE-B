# DEPLOYMENT

## v7 Deployment Options

### Option A — Docker Compose (recommended for first real infra step)
At repository root:
```bash
make up
```
This starts:
- postgres
- backend

### Option B — manual local/VPS process
1. Set up PostgreSQL
2. Copy `backend/.env.example` to `backend/.env`
3. Install dependencies
4. Run migrations
5. Seed demo data if desired
6. Start backend

## Backend env
Use PostgreSQL-first config in production-like environments.
Prefer:
- `USE_POSTGRES=true`
- `DATABASE_URL=` empty
- explicit Postgres credentials set

## Notes
- v7 still keeps SQLite fallback for convenience
- production should prefer PostgreSQL and real secrets
- Google auth is still a skeleton
