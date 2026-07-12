# Future

> **Status:** *Future* = ideas only. No design, no schema, no commitment.
> This is the canonical "not being built" list. See [DECISIONS.md D7](./DECISIONS.md)
> for the difference between **Active / Hardening / Deferred / Future**.

Items here are intentionally under-specified. When one becomes real, it gets an
RFC and moves to [TODO.md](./TODO.md).

---

## Collaboration

- **Team memberships and roles** — a `memberships` table mapping users to shared
  workspaces with roles (owner / editor / viewer). Currently every workspace has
  exactly one `owner_id`.
- **Org / workspace switching UI** — once multi-workspace exists beyond the
  default personal shelf.

## Distribution

- **Custom domains** — map a user domain to their public pages, with TLS. Likely
  a CNAME → CDN flow.
- **Embed product surface** — a documented iframe embed policy (sandbox,
  `sandbox` attrs, per-item embed flags) for embedding `/p/{id}` in Notion/Slack.
- **OG/social preview images** ([TODO H7](./TODO.md)) — generated preview cards.
  Named but no design; could graduate from Track H to its own note.

## Economics

- **Paid tier / billing** — 50 GB+ storage, permanent public pages, higher limits.
  Needs an entitlement + payments integration (no design yet).
- **R2 / egress-free storage** — Cloudflare R2 sync to drop public-read egress
  cost. Infrastructure idea only.

## Auth & API

- **Token scopes** — granular scopes (`workspace:read`, `publish`, per-workspace).
  v1 is full-access only; see [DECISION D3](./DECISIONS.md).
- **Guest / try-without-signup** — anonymous workspace reclaimed via
  `reclaim_key`. Schema ready; explicitly **not** MVP ([D1](./DECISIONS.md)).
- **SSO / additional IdPs** — beyond the default Firebase path.

## Platform

- **Async job queue (general)** — `arq`/queue shared across tools and (if ever
  revived) the deferred pipeline. Today each tool runs sync until one needs async
  ([RFC-0003 §5](./rfc/0003-pluggable-tools.md)).
- **Token streaming / webhooks** — notify clients when an async tool completes.

## Explicit non-goals (do not chase)

These are listed so they are not re-proposed by accident:

- **Community widget marketplace** — premature; tools are first-party only for
  now ([RFC-0003 §9](./rfc/0003-pluggable-tools.md)).
- **Full app/site builder** (v0/Lovable-style) — BamiTools ships owned HTML
  artifacts from workflows, not whole applications
  ([introduction.md — What it is not](./introduction.md)).
- **Chat as the primary interface** — deferred ([RFC-0005](./rfc/0005-deferred-chat-telegram.md));
  chat may become a channel into the same shelf, never the product identity.

---

## From here

When a Future item becomes real:

1. Write an RFC under `docs/rfc/`.
2. Add a row to the relevant Track in [TODO.md](./TODO.md).
3. Remove it from this file (or mark it *graduated* with a link).
