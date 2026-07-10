# ── Stage 1: build the SPA ──────────────────────────────────────────
FROM node:24-alpine AS web-build
WORKDIR /build
ENV CI=true
RUN corepack enable && corepack prepare pnpm@10.13.1 --activate
COPY snapbami-web/package.json snapbami-web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY snapbami-web/ ./
RUN pnpm build

# ── Stage 2: Python server + bundled SPA ────────────────────────────
FROM python:3.13-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

COPY snapbami-server/pyproject.toml snapbami-server/uv.lock snapbami-server/README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY snapbami-server/src ./src
RUN uv sync --frozen --no-dev
# Bundle the built SPA so the server can serve it directly
COPY --from=web-build /build/dist ./static

ENV STATIC_DIR=/app/static
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "snapbami_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
