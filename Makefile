.PHONY: up down logs backend admin customer migrate seed deploy workers

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
