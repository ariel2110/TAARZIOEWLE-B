.PHONY: up down logs backend admin customer migrate seed deploy workers celery beat test lint ci

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

backend:
	cd backend && uvicorn app.main:app --reload

admin:
	cd frontend-admin && npm install && npm run dev

customer:
	cd frontend-customer && npm install && npm run dev

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.db.seed_cli

deploy:
	bash scripts/deploy.sh

workers:
	bash scripts/run_workers.sh

celery:
	cd backend && celery -A app.core.celery_app worker --loglevel=info --concurrency=2 -Q sitenest

beat:
	cd backend && celery -A app.core.celery_app beat --loglevel=info

# ── Quality ──────────────────────────────────────────────────────────────────

test:
	cd backend && python -m pytest tests/ -q --tb=short

lint:
	cd backend && ruff check app/

ci: lint test
	cd frontend-admin   && npm ci && npm run build
	cd frontend-customer && npm ci && npm run build
	cd frontend-public  && npm ci && npm run build
