# RFC-0002: API Tokens & MCP

> **Status:** Draft · **Active**  
> **Author:** Quan  
> **Created:** 2026-07-12  
> **Last Updated:** 2026-07-12  
> **Depends on:** [RFC-0001](./0001-core-platform.md) (auth, workspaces, publish)  
> **Note:** Former RFC-0002 (chat/Telegram) moved to [RFC-0005](./0005-deferred-chat-telegram.md)

---

## 1. Thesis

External agents (Cursor, Claude Desktop, CLI scripts) need the same workspace powers as a logged-in user **without** a browser session.

BamiTools issues **API tokens** (`btk_…`) bound to a user. An **MCP server** exposes list / read / write / publish over those tokens so any MCP-compatible client can stock the shelf and publish.

---

## 2. API tokens

### 2.1 Storage (`access_tokens`)

| Column | Role |
|---|---|
| `user_id` | Owner |
| `label` | User-facing name (e.g. "Cursor MCP") |
| `key_hash` | SHA-256 of full token (unique) |
| `key_prefix` | Display prefix only (e.g. `btk_abc1…`) |
| `is_active` | Soft revoke |
| `last_used_at` | Audit |
| `expires_at` | Optional expiry |

Full token is shown **once** at creation. Only the hash is stored.

### 2.2 Format

- Prefix: `btk_`
- High-entropy secret body (e.g. 32+ bytes url-safe)
- Header: `Authorization: Bearer btk_…`

### 2.3 Lifecycle REST (auth: session JWT)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/tokens` | Create token → return full secret once |
| `GET` | `/api/tokens` | List prefixes, labels, last_used (no secrets) |
| `DELETE` | `/api/tokens/{id}` | Revoke (`is_active = false`) |

### 2.4 Scopes (v1)

v1: token has **full access** to all workspaces owned by the user (same as the user session).

Future: scopes such as `workspace:read`, `workspace:write`, `publish`, per-workspace restriction.

### 2.5 Auth resolution order

1. `Authorization: Bearer btk_…` → lookup hash → user  
2. Else IdP JWT / session → user  
3. Else 401  

Update `last_used_at` on successful token auth (throttled if needed).

---

## 3. MCP surface

### 3.1 Tools

| Tool | Input | Behavior |
|---|---|---|
| `list_workspace_files` | optional directory | List paths under user's default (or selected) workspace |
| `read_workspace_file` | path | Return file content from private bucket |
| `write_workspace_file` | path, content | Write private object + upsert `workspace_items` |
| `publish_item` | path | Publish → return `/p/{public_id}` |

Optional later: `run_tool` for [RFC-0003](./0003-pluggable-tools.md).

### 3.2 Workspace selection

v1: operate on the user's **default** personal workspace.  
Later: parameter `workspace_id` or `workspace_slug` if multi-workspace UI exists.

### 3.3 Transport

- Prefer **SSE** (or stdio for local proxy) per MCP server conventions used by Cursor/Claude Desktop.
- Server validates Bearer token on connect or per request.

### 3.4 Errors

| Case | Result |
|---|---|
| Missing/invalid token | Unauthorized |
| Path outside workspace / traversal | 400/403 |
| Publish of missing path | 404 |
| Rate limited | 429 |

---

## 4. Rate limiting

- Apply per-user (and optionally per-token) limits on write + publish.
- Guests/IP-only limits are secondary; authenticated multi-tool platform uses user quotas.
- Record significant actions in `usage_log` when telemetry is wired.

---

## 5. Security

- Never log full tokens; log `key_prefix` only.
- Rotate: create new token, revoke old.
- HTTPS only in production.
- Tokens must not work across users; always resolve `user_id` then enforce `workspaces.owner_id`.
- MCP process holds token like a password — document storage in client config carefully.

---

## 6. Relationship to other RFCs

| RFC | Role |
|---|---|
| [0001](./0001-core-platform.md) | Authz + storage + publish semantics MCP calls into |
| [0003](./0003-pluggable-tools.md) | Optional `run_tool` MCP tool later |
| [0005](./0005-deferred-chat-telegram.md) | Chat may reuse same workspace tools; not v1 |

---

## 7. Open questions

1. Fine-grained scopes before multi-tenant abuse appears.
2. Whether MCP runs in-process with FastAPI or as a separate process sharing auth middleware.
3. Default rate limit numbers for free vs paid tiers.
