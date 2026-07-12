# Database Guide

## Overview

PostgreSQL 18 with asyncpg. Migrations are plain SQL files, applied in order by a lightweight Python runner. No heavy framework (Alembic, Flyway) — just sorted `.sql` files tracked in a `_migrations` table.

## Schema layout

```
bamitools-server/src/bamitools_server/db/migrations/
├── 001_core.sql            # users + workspaces + workspace_items
├── 002_credentials.sql     # byok_keys + access_tokens + system_credentials
├── 003_chat.sql            # conversations + messages + attachments  [DEFERRED app use]
├── 004_telemetry.sql       # usage_log + reports
└── 005_pipeline_runs.sql   # pipeline_runs  [DEFERRED app use]
```

Each file is self-contained: table definitions + their indexes together. Files run in alphabetical order. Foreign key dependencies must be respected (tables referenced must be defined earlier).

## Tables by status

### Core (active product path)

| Table | File | Purpose |
|---|---|---|
| `users` | 001_core | Identity, tier; IdP `auth_uid` → internal UUID |
| `workspaces` | 001_core | Shelves owned by users |
| `workspace_items` | 001_core | Private files and published pages |
| `access_tokens` | 002_credentials | API tokens for MCP/CLI (hashed) — [RFC-0002](./rfc/0002-mcp-and-tokens.md) |
| `byok_keys` | 002_credentials | User LLM keys (tools later) — [RFC-0007](./rfc/0007-byok.md) |
| `system_credentials` | 002_credentials | Platform secrets |
| `usage_log` | 004_telemetry | Billing/analytics actions |
| `reports` | 004_telemetry | Content moderation reports |

### Deferred (schema may exist; no app feature yet)

| Table | File | When |
|---|---|---|
| `conversations` | 003_chat | [RFC-0005](./rfc/0005-deferred-chat-telegram.md) |
| `messages` | 003_chat | RFC-0005 |
| `attachments` | 003_chat | RFC-0005 |
| `pipeline_runs` | 005_pipeline_runs | [RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md) |

Do not build product features on deferred tables until those RFCs leave Deferred status.

## Conventions

- **TEXT everywhere** — no VARCHAR(N) or CHAR(N). Postgres TEXT has identical performance.
- **UUID v7 primary keys** — `UUID DEFAULT uuidv7()`. Time-sortable.
- **TIMESTAMPTZ** for all timestamps. Always `DEFAULT NOW()`.
- **JSONB** for flexible metadata (`workspace_items.meta`, `pipeline_runs.prompt_versions`).
- **Decoupled User Identity** — internal UUID `id`; never FK to raw Firebase UID elsewhere.
- **Conditional Uniqueness Indexes** — workspace paths unique per workspace; owner+slug unique when owned.

## workspace_items.mode (v1)

| Value | Use |
|---|---|
| `raw` | Source uploads / pastes |
| `html` | Finished HTML artifacts |
| `pipeline` | **Reserved** for deferred multi-agent outputs (RFC-0004) |

## Notable workspace_items columns

Some columns exist in core schema but are gated by policy or a later track:

| Column | Status | Reference |
|---|---|---|
| `password_hash` | Core column; `/s/` route is Track H5 | [RFC-0006](./rfc/0006-secure-share.md) |
| `reclaim_key` | Active — guest claim lookup key (unique) | [DECISIONS.md D9](./DECISIONS.md) |
| `public_id` | Core | Set on publish (`/p/`) and optionally on share (`/s/`) |

## 001_core.sql Layout

```sql
CREATE TABLE IF NOT EXISTS users (
    id               UUID DEFAULT uuidv7() PRIMARY KEY,
    auth_provider    TEXT DEFAULT 'firebase',
    auth_uid         TEXT UNIQUE NOT NULL,
    username         TEXT UNIQUE,
    display_name     TEXT,
    email            TEXT UNIQUE,
    tier             TEXT DEFAULT 'free',
    telegram_chat_id BIGINT UNIQUE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    owner_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    meta            JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspace_items (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    path            TEXT NOT NULL,
    public_id       TEXT UNIQUE,
    title           TEXT,
    content_hash    TEXT,
    mode            TEXT NOT NULL,                      -- v1: 'html' | 'raw' ('pipeline' reserved)
    reclaim_key     TEXT,
    password_hash   TEXT,
    meta            JSONB DEFAULT '{}',
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (workspace_id, path)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_workspaces_owner_slug
    ON workspaces(owner_id, slug) WHERE owner_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_workspaces_anon_slug
    ON workspaces(slug) WHERE owner_id IS NULL;
```

## Running migrations

### Via Docker (automatic)

Migrations run automatically on `docker compose up`. The `migrate` service is a one-shot container that runs before the server starts:

```bash
docker compose up -d
```

### Local development

```bash
make migrate
```

This runs `scripts/migrate.py`.

## Creating a new migration

```bash
ls bamitools-server/src/bamitools_server/db/migrations/
```

Next file: `006_<descriptive_name>.sql`.

## Altering existing tables

```sql
-- 006_add_page_views.sql
ALTER TABLE workspace_items ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;
```

**Never edit an already-applied migration file.** The runner records applied filenames in `_migrations` and will skip them. Create a new file instead.
