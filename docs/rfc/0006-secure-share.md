# RFC-0006: Secure Share (`/s/`)

> **Status:** Draft · **Hardening (Track H5)** — not MVP
> **Author:** Quan
> **Created:** 2026-07-12
> **Depends on:** [RFC-0001](./0001-core-platform.md) (storage, `workspace_items`)
> **Resolves:** [DECISIONS.md D5](../DECISIONS.md)

---

## 1. Thesis

Some files should be shareable **without** becoming public. Secure share serves a
file from the **private** bucket behind a password, so it is never copied to the
public CDN bucket and never appears at `/p/{id}`.

One line: **`/s/{public_id}` + password → short-lived cookie → stream from private storage.**

This is **Track H5**, after the MVP public publish loop (C1–C7).

---

## 2. When to use `/s/` vs `/p/`

| Need | Use |
|---|---|
| Anyone with the link, CDN-fast, permanent-ish | `/p/{public_id}` (public bucket) |
| Restricted to people who know a password; not on the public bucket | `/s/{public_id}` |

A single item can be shared via `/s/` without ever being published to `/p/`.

---

## 3. Data model

Uses existing columns on `workspace_items` — **no migration required**:

| Column | Use |
|---|---|
| `public_id` | The share handle (same space as publish; must be set for `/s/` to exist) |
| `password_hash` | Argon2id hash of the share password |

Invariants:

- `/s/{public_id}` is valid only when `password_hash IS NOT NULL`.
- Setting a password does **not** copy the object to the public bucket. The object
  stays at `s3://bamitools-private/{workspace_id}/{path}`.
- An item may have both a public publish and a password — they are independent.
  `/p/` serves the public copy; `/s/` serves the private copy gated by password.

---

## 4. Flow

```text
GET /s/{public_id}
  │
  ▼
lookup workspace_items by public_id
  ├─ not found / no password_hash  → 404
  ▼
has valid share cookie for this public_id?
  ├─ yes → stream object from private bucket (Range-aware) → 200
  ▼ no
render password prompt (HTML form or JSON 401)
  │
POST /s/{public_id}  { password }
  │
  ▼
verify Argon2id(password, password_hash)
  ├─ mismatch → 401 (constant-time, throttled)
  ▼ ok
set signed short-lived cookie scoped to /s/{public_id}
→ stream object
```

---

## 5. Cookie

- **Name:** e.g. `bts_{public_id}` (per-item, not global).
- **Value:** server-signed (HMAC) token carrying `public_id` + expiry.
- **Scope:** path `/s/{public_id}` only — cannot be used for any other share or
  for auth as the owner.
- **TTL:** short (e.g. session, or a few hours). Renewable by re-entering the
  password.
- **Flags:** `HttpOnly`, `Secure`, `SameSite=Strict`.

This is **not** an auth session. It grants exactly one capability: streaming this
one private object for a brief window.

---

## 6. Storage & CDN

- `/s/` requests **must hit FastAPI** (cookie validation + private bucket read).
  They are **not** CDN-direct like `/p/`.
- Optionally stream through a signed/private S3 URL; never expose the bucket
  directly.
- Cost posture: more app compute than `/p/`, so rate-limit per `public_id` and
  per IP to blunt brute force and abuse.

---

## 7. Setting a password

- Web UI / API: `POST /api/w/{workspace_id}/items/{id}/share` with a password →
  sets `password_hash` and assigns a `public_id` if none exists.
- Remove share: clear `password_hash` (optionally revoke `public_id`). Existing
  cookies become invalid because there is nothing to grant.

---

## 8. Security

- **Argon2id** for `password_hash`, not bcrypt/PBKDF2.
- Constant-time compare; throttle failures per `public_id` + IP (e.g. exponential
  backoff, capped).
- Never log passwords. Log only `public_id` + success/failure.
- The cookie is the only capability — stealing it gives access to one file, not
  the workspace.
- `/s/` responses carry a strict CSP and `Cache-Control: no-store`.

---

## 9. Non-goals

- Per-recipient ACLs / "share with user X" (that is teams — [Future](../FUTURE.md)).
- Time-limited magic links without a password (future enhancement).
- Streaming ranges beyond what S3 supports natively.

---

## 10. Open questions

1. Whether a share can be revoked independently of clearing the password (e.g.
   rotate the `public_id` while keeping the password).
2. Default cookie TTL (session vs N hours).
3. Rate-limit numbers for failures per `public_id`.
