# Build Tracker

Product focus: **auth + workspaces + publish**, then **MCP/tokens**, then **pluggable tools**.
LangGraph pipeline and chat/Telegram are **deferred** (not on the critical path).

## Status taxonomy (canonical)

Every feature in these docs is in exactly one status. See [DECISIONS.md D7](./DECISIONS.md).

| Status | Meaning | Lives in |
|---|---|---|
| **Active** | On the build path now | Tracks C / T below; [RFC 0001–0003](./rfc/0001-core-platform.md), [0006–0007](./rfc/0006-secure-share.md) |
| **Hardening** | Named, thin spec; after/alongside MVP | Track H below |
| **Deferred** | Full design exists; explicitly parked | [RFC 0004–0005](./rfc/0004-deferred-langgraph-pipeline.md); Track D below |
| **Future** | Idea only; no design | [FUTURE.md](./FUTURE.md) |

Resolved policy questions: [DECISIONS.md](./DECISIONS.md) (auth-first, BYOK, scopes, publish, `/s/`, abuse).

RFCs: [0001 core](./rfc/0001-core-platform.md) · [0002 MCP/tokens](./rfc/0002-mcp-and-tokens.md) · [0003 tools](./rfc/0003-pluggable-tools.md) · [0006 secure share](./rfc/0006-secure-share.md) · [0007 BYOK](./rfc/0007-byok.md) · [0004 LangGraph deferred](./rfc/0004-deferred-langgraph-pipeline.md) · [0005 chat deferred](./rfc/0005-deferred-chat-telegram.md)

---

## Track C — Core (MVP)

Goal: Authenticated user (or API token) writes private files → publishes → `/p/{id}` works globally.

| Step | What | Status |
|---|---|---|
| C1 | Auth: JWT → upsert `users` + default personal workspace | [ ] |
| C2 | PUT/GET private workspace files (owner authz) → `bamitools-private` | [ ] |
| C3 | POST publish → `bamitools-public` + content URL (`/p/{id}` or `PAGES_BASE_URL/{id}`) | [ ] |
| C4 | API tokens: create / list / revoke + Bearer auth | [ ] |
| C5 | Rate limiting (per user / IP) | [ ] |
| C6 | MCP server — list / read / write / publish | [ ] |
| C7 | Deploy — Docker + CDN direct-read for content domain | [ ] |
| C8 | Guest trial: two-link publish + `/claim?token=` reclaim route ([D9](./DECISIONS.md)) | [ ] |
| C9 | CSP `sandbox allow-scripts; connect-src 'none'; form-action 'none'` on all published HTML ([D6](./DECISIONS.md)) | [ ] |

**MVP = C1–C9** (C8–C9 bring guest + universal sandbox into the wedge).

---

## Track T — Pluggable tools

Goal: Thin converters write HTML into the workspace. Depends on Core.

| Step | What | Depends on | Status |
|---|---|---|---|
| T0 | Tool runner registry + `POST /api/tools/{id}` | C2, C3 | [ ] |
| T1 | First tool (e.g. article → HTML slides) | T0 | [ ] |
| T2 | Second tool (e.g. PDF → HTML) | T0 | [ ] |
| T3 | Optional MCP `run_tool` | C6, T0 | [ ] |

Design: [RFC-0003](./rfc/0003-pluggable-tools.md).

---

## Track H — Hardening

Independent hardening after or alongside core. Auth-first deps where noted.
Designs: [RFC-0006](./rfc/0006-secure-share.md) (`/s/`), [RFC-0007](./rfc/0007-byok.md) (BYOK).

| Step | What | Depends on | Status |
|---|---|---|---|
| H1 | Storage quota enforcement (1/5/50 GB) + anonymous 3-day expiry cron | C1 | [ ] |
| H2 | Frontend (workspace explorer, publish UI) | C2 | [ ] |
| H3 | Monitoring (OTel, metrics, alerting) | C1 | [ ] |
| H4 | Content moderation (report endpoint, Safe Browsing scan, blocklist) — builds on the universal sandbox ([D6](./DECISIONS.md)) | C3 | [ ] |
| H5 | Secure share `/s/` password validation ([RFC-0006](./rfc/0006-secure-share.md)) | C2 | [ ] |
| H6 | Profiles + username registration | C1 | [ ] |
| H7 | OG preview images | C3 | [ ] |

---

## Track D — Deferred (not critical path)

| Item | Spec | Status |
|---|---|---|
| Multi-agent LangGraph pipeline | [RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md) | Deferred |
| Chat UI + Telegram bot | [RFC-0005](./rfc/0005-deferred-chat-telegram.md) | Deferred |
| Widget SSG factory / eval suite | inside [RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md) | Deferred |

Do **not** start Track D until Core is dogfooded and tools (if needed) are insufficient.
Idea-stage items (teams, custom domains, billing, etc.) live in [FUTURE.md](./FUTURE.md), not here.

---

## Already built

| Component | Status |
|---|---|
| Phase 00 scaffold (server, web, Docker) | [x] |
| Phase 01 DB + storage scaffold (Postgres, Redis, S3) | [x] |
| Local read path for public files | [x] |
| html_loader template | [x] |
| RFC set reorganized (core / MCP / tools / deferred) | [x] |

---

## Critical path

```
C1 → C2 → C3 → C4 → C5 → C6 → C7 → C8 → C9 → MVP
                              ↘ T0 → T1 → T2
                     H* (parallel as needed)
```

No LangGraph or chat branch on the MVP path.
