# ── Stage 1: build the SPA ──────────────────────────────────────────
FROM node:24-alpine AS web-build
WORKDIR /build
ENV CI=true
RUN corepack enable && corepack prepare pnpm@10.13.1 --activate
COPY bamitools-web/package.json bamitools-web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY bamitools-web/ ./
RUN pnpm build

# ── Stage 2: Python server + bundled SPA ────────────────────────────
FROM python:3.13-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

COPY bamitools-server/pyproject.toml bamitools-server/uv.lock bamitools-server/README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY bamitools-server/src ./src
COPY bamitools-server/scripts ./scripts
RUN uv sync --frozen --no-dev
# Bundle the built SPA so the server can serve it directly
COPY --from=web-build /build/dist ./static

ENV STATIC_DIR=/app/static
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "bamitools_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
