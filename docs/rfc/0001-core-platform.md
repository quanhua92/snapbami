# RFC-0001: Core Platform — Auth, Workspaces, Storage, Publish

> **Status:** Draft · **Active**  
> **Author:** Quan  
> **Created:** 2026-07-11  
> **Last Updated:** 2026-07-12  
> **Depends on:** Phase 01 (DB + storage scaffold)  
> **Related:** [RFC-0002](./0002-mcp-and-tokens.md) (API tokens + MCP), [RFC-0003](./0003-pluggable-tools.md) (tools)  
> **Deferred:** [RFC-0004](./0004-deferred-langgraph-pipeline.md) (LangGraph), [RFC-0005](./0005-deferred-chat-telegram.md) (chat/Telegram)

---

## 1. Thesis

BamiTools is an **authenticated workspace and HTML hosting platform**.

**The system in one sentence:** Users and agents collaborate on private drafts (`/w/`), publish clean-URL pages (`/p/`) to a public CDN-mapped S3 bucket, and optionally share password-locked pages (`/s/`) from the private bucket.

Creation paths for v1:

1. **User or agent writes files** into a private workspace (web UI, REST, or MCP).
2. **Publish** copies/renders a file to the public bucket → shareable `/p/{public_id}`.

Optional later: pluggable tools ([RFC-0003](./0003-pluggable-tools.md)) and deferred multi-agent pipeline ([RFC-0004](./0004-deferred-langgraph-pipeline.md)). Chat is not the primary interface ([RFC-0005](./0005-deferred-chat-telegram.md)).

---

## 2. Core request lifecycle

```
Authenticated user / agent
  │
  ▼
┌──────────────────┐
│  Authn / Authz   │  JWT session or Bearer API token → users.id
│                  │  Workspace ownership check
└──────┬───────────┘
       ▼
┌──────────────────┐
│  Workspace I/O   │  PUT/GET private file
│                  │  s3://bamitools-private/{workspace_id}/{path}
│                  │  + workspace_items row
└──────┬───────────┘
       ▼
┌──────────────────┐
│  Publish         │  Copy/render → bamitools-public/{public_id}
│  (optional)      │  Assign public_id; serve via CDN at /p/{id}
└──────────────────┘
```

Basic limits (size, rate) apply on write/publish. Full PII/injection/LLM guardrails belong to deferred pipeline/tools that call LLMs.

---

## 3. Authentication & authorization

### 3.1 Identity

- External IdP (Firebase or equivalent) issues JWTs.
- Server verifies JWT → upserts `users` by `(auth_provider, auth_uid)`.
- All relations use internal `users.id` (UUID v7), never the external UID alone.

### 3.2 Default workspace

On first successful login, create a personal workspace if none exists:

- `owner_id = users.id`
- `slug = 'default'` (or similar)
- Unique per owner via `uq_workspaces_owner_slug`

### 3.3 Auth mechanisms

| Mechanism | Use |
|---|---|
| Browser session / IdP JWT | Web SPA |
| API token `Bearer btk_…` | MCP, CLI, automation — details in [RFC-0002](./0002-mcp-and-tokens.md) |

### 3.4 Authorization rules

- **Workspace routes** (`/w/`, publish): caller must own the workspace (`workspaces.owner_id = users.id`).
- **Public routes** (`/p/`): no auth; CDN/static.
- **Secure share** (`/s/`): password check against `workspace_items.password_hash` (hardening track; not MVP-critical).

### 3.5 Guest path (zero-friction trial funnel)

Guest is a first-class MVP path, not deferred ([D1](../DECISIONS.md)). A guest
(anonymous web paste, or MCP in guest mode) creates a draft and receives **two
links** ([D9](../DECISIONS.md)):

- **View:** `{PAGES_BASE_URL or /p}/{public_id}` — renders for anyone with the
  unguessable URL; sandboxed (D6); 3-day TTL (D8).
- **Claim:** `{app origin}/claim?token={reclaim_key}` — app-served; looks up the
  draft by `reclaim_key`; log in to move it into a real workspace.

Viewing ≠ claiming: only the `reclaim_key` holder (the creator) can claim. An
authenticated publish (token MCP / logged-in web) writes straight to a clean
content URL with no claim step.

---

## 4. Two-bucket storage

### 4.1 Isolation

| Bucket | Access | Contents |
|---|---|---|
| `bamitools-public` | Public read | Published pages at `{public_id}` |
| `bamitools-private` | Block public access | `{workspace_id}/{filepath}` drafts |

### 4.2 URL space

`PAGES_BASE_URL` (env, `.env.example`) selects same-origin vs dedicated content
domain. Empty → `/p/{public_id}` on the app origin. Set (hosted = `https://bami.page`)
→ CDN-direct to S3 with the D6 CSP header at the edge, zero app compute.

| Route | Backend | Auth |
|---|---|---|
| `/w/{workspace_id}/{filepath}` | FastAPI → private bucket | Owner session or API token |
| `{PAGES_BASE_URL or /p}/{public_id}` | CDN → public bucket (CSP header at edge) *or* app (if unset) | None |
| `/claim?token={reclaim_key}` | FastAPI → guest reclaim | reclaim_key + login |
| `/s/{public_id}` | FastAPI → private stream | Password |

### 4.3 S3 layout

```
s3://bamitools-public/
└── {public_id}                    # published static HTML (or object key convention)

s3://bamitools-private/
└── {workspace_id}/
    └── notes/
        └── todo.md
```

---

## 5. Publishing model

Staging and production are decoupled:

1. **Staging:** Write privately under `/w/{workspace_id}/{path}`.
2. **Publish:** `POST …/publish` on a path (or equivalent).
3. **Execution:** Copy/render to `bamitools-public/{public_id}`; set `workspace_items.public_id`.
4. **Production:** Live at `/p/{public_id}` under CDN caching.

Viewers of public pages should not require FastAPI compute (CDN direct-read).

---

## 6. Data model (core)

### 6.1 Tables in scope

| Table | Role |
|---|---|
| `users` | Identity, tier, optional telegram_chat_id (unused until RFC-0005) |
| `workspaces` | Owned shelves |
| `workspace_items` | Files / published pages |
| `access_tokens` | Agent tokens — [RFC-0002](./0002-mcp-and-tokens.md) |
| `byok_keys` | Optional later for tool LLM costs |
| `usage_log` / `reports` | Telemetry / moderation hooks |

### 6.2 Schema sketch

```sql
CREATE TABLE users (
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

CREATE TABLE workspaces (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    owner_id        UUID REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    meta            JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workspace_items (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    path            TEXT NOT NULL,
    public_id       TEXT UNIQUE,
    title           TEXT,
    content_hash    TEXT,
    mode            TEXT NOT NULL,   -- v1: 'raw' | 'html'; 'pipeline' reserved (RFC-0004)
    reclaim_key     TEXT,
    password_hash   TEXT,
    meta            JSONB DEFAULT '{}',
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (workspace_id, path)
);
```

Canonical detail: [db.md](../db.md) and migrations under `bamitools-server/.../db/migrations/`.

### 6.3 Item modes (v1)

| `mode` | Meaning |
|---|---|
| `raw` | Uploaded/pasted source (md, csv, pdf bytes metadata, etc.) |
| `html` | Finished HTML artifact (ready or published) |
| `pipeline` | **Reserved** for deferred LangGraph outputs (RFC-0004) |

---

## 7. REST surface (core)

| Method | Path | Purpose |
|---|---|---|
| — | Auth middleware | JWT or Bearer token → user |
| `PUT` | `/api/w/{workspace_id}/raw/{filepath}` | Upload private file |
| `GET` | `/api/w/{workspace_id}/raw/{filepath}` | Read private file |
| `POST` | `/api/w/{workspace_id}/publish` | Deploy path → public_id |
| `GET` | `/p/{public_id}` | Public page (CDN) |
| `GET` | `/s/{public_id}` | Password share (later) |

MCP tools mirror list/read/write/publish — [RFC-0002](./0002-mcp-and-tokens.md).

---

## 8. Security

- Owner-only access to private workspace objects.
- Public HTML: CSP at edge; sanitize where platform generates HTML.
- Raw user HTML hosting is abuse-sensitive — rate limits + moderation track (Track H in [TODO.md](../TODO.md)).
- Never log raw API tokens or IdP secrets.

---

## 9. Cost model (platform)

| Path | Cost posture |
|---|---|
| Public `/p/` views | CDN → public bucket; ~$0 FastAPI |
| Private I/O | App + S3 + Postgres |
| Free tier storage | Per-user quota (1 GB free / 5 GB BYOK); no inactivity purge |
| Anonymous (if shipped) | 3-day `expires_at` expiry; reclaimable on signup |
| Paid | Larger quota (50 GB+) + permanent pages |

LLM cost appears only when tools or deferred pipeline run; BYOK keeps platform compute at $0 for those paths.

---

## 10. Open questions (core only)

1. Team workspaces / membership table (see [FUTURE.md](../FUTURE.md)).
2. Redirects when `public_id` is revoked or replaced.
3. Guest/reclaim mechanics — resolved: see [DECISIONS.md D1](../DECISIONS.md) and [D9](../DECISIONS.md) (guest is the MVP trial funnel; view + claim two-link model).

---

## 11. Non-goals (this RFC)

- Multi-agent LangGraph pipeline → [RFC-0004](./0004-deferred-langgraph-pipeline.md)
- Chat UI / Telegram → [RFC-0005](./0005-deferred-chat-telegram.md)
- Tool runner implementation details → [RFC-0003](./0003-pluggable-tools.md)
