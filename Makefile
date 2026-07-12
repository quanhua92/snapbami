.PHONY: dev-server dev-web dev build-web up down psql migrate test e2e

dev-server:
	cd bamitools-server && uv run uvicorn bamitools_server.main:app --reload --port 8000

dev-web:
	cd bamitools-web && pnpm dev

build-web:
	cd bamitools-web && pnpm build

migrate:
	cd bamitools-server && \
	DATABASE_URL="postgresql://bamitools:changeme@localhost:5432/bamitools" \
	uv run python scripts/migrate.py

test:
	cd bamitools-server && uv run pytest tests/ -v

e2e:
	cd bamitools-server && \
	DATABASE_URL="postgresql://bamitools:changeme@localhost:5432/bamitools" \
	REDIS_URL="redis://localhost:6379/0" \
	S3_ENDPOINT_URL="http://localhost:9000" \
	S3_ACCESS_KEY="rustfsadmin" \
	S3_SECRET_KEY="rustfsadmin" \
	uv run python scripts/test-e2e.py

up:
	docker compose up -d --build

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

down:
	docker compose down

down-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

psql:
	docker compose exec postgres psql -U $$POSTGRES_USER bamitools
