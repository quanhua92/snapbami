# BamiTools

Authenticated workspaces for private files and published HTML pages. MCP and API tokens for agents.

See [docs/introduction.md](docs/introduction.md), [docs/TODO.md](docs/TODO.md),
[docs/DECISIONS.md](docs/DECISIONS.md) (resolved policy), and [docs/FUTURE.md](docs/FUTURE.md) (ideas).

## Setup

```bash
cp .env.example .env
git config core.hooksPath githooks   # enable pre-commit hook (ruff check + format)
```

## Development

Two terminals:

```bash
make dev-server   # FastAPI on :8000
make dev-web      # Vite dev server on :5173
```

## Commands

| Command | What it does |
|---|---|
| `make dev-server` | Run FastAPI with hot reload |
| `make dev-web` | Run Vite dev server |
| `make build-web` | Build SPA to `dist/` |
| `make up` | `docker compose up -d --build` (web + redis + postgres) |
| `make down` | Stop all dev containers |
| `make up-prod` | Start with caddy (TLS on 80/443) |
| `make down-prod` | Stop prod containers |
| `make psql` | Connect to PostgreSQL in Docker |

## Docker (full stack)

```bash
make up
curl localhost:8000/api/health   # {"status":"ok"}
make down
```

## Project layout

```
bamitools-server/src/bamitools_server/   # FastAPI app (config, main)
bamitools-web/src/                       # React SPA (routes, components)
```
