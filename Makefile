.PHONY: dev-server dev-web dev build-web up down psql

dev-server:
	cd snapbami-server && uv run uvicorn snapbami_server.main:app --reload --port 8000

dev-web:
	cd snapbami-web && pnpm dev

build-web:
	cd snapbami-web && pnpm build

up:
	docker compose up -d --build

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

down:
	docker compose down

down-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

psql:
	docker compose exec postgres psql -U $$POSTGRES_USER snapbami
