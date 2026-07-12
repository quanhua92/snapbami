# Decisions

> Resolved policy and architecture questions. Each entry is a decision, not a
> proposal — when one changes, update it here and note why in the commit.

Style: **ADR-lite**. One section per decision: context → decision → consequences.

---

## D1 — Auth is the primary path; guest is the zero-friction trial funnel

**Context.** Two creation paths coexist: an **authenticated** one (the durable,
owned, full-featured path) and an **anonymous/guest** one (zero signup, ephemeral,
conversion-oriented). Guest was earlier deferred; it returns to the MVP because the
zero-friction "paste → get a link" moment is the sharpest wedge, and the abuse
surface is controllable (D6, D9).

**Decision.**
- **Authenticated** is the primary, full path: real `owner_id`, storage quota
  (D8), tokens, MCP, publish to a content URL (sandboxed per [D6](#)).
- **Guest** is a first-class **trial funnel** in the MVP:
  - Paste or agent-publish with no account → get two links — a **view** link
    (public-by-unguessable-URL, sandboxed, 3-day TTL) and a **claim** link
    (app-served, one-time). See [D9](#) for the exact URLs/mechanics.
  - Viewing is open to anyone with the view link; **claiming** requires the
    `reclaim_key` (only the creator holds it) → no claim-theft race.
  - Sign up (one click) → the draft moves into the new account's workspace.
- Auth is **not** a prerequisite for creating/viewing; it is the upgrade to
  owning and persisting beyond 3 days.
- Schema (`reclaim_key`, `expires_at`, anon-slug index) all active.

**Consequences.**
- The MCP ships in two modes: **token mode** (authenticated → publish straight to
  a content URL — sandboxed per [D6](#), just no claim step) and **guest mode** (no token → two-link trial output).
- Auth stays the recommended path; guest is bounded by per-IP rate limits + 3-day
  TTL + the universal sandbox (D6).
- "Auth-first" no longer means "no guest"; it means *auth is the durable path,
  guest is the trial.*

---

## D2 — BYOK is a Tools-track concern, not deferred

**Context.** BYOK ("bring your own key") was originally nested under the deferred
LangGraph model gateway. With the pivot to pluggable tools (RFC-0003),
LLM cost shows up the moment a tool calls a model — well before any multi-agent
pipeline. BYOK therefore cannot wait for RFC-0004.

**Decision.**
- BYOK ownership lives in active design under **[RFC-0007](./rfc/0007-byok.md)**.
- Default: tools use the **platform key** (metered, capped on free tier).
- Opt-in: a user stores a key in `byok_keys`; tools that find a usable key prefer
  it and grant higher/no caps. LLM cost then bypasses the platform.
- BYOK is **not required** for the core publish loop (C1–C7). It is first needed
  at Track T (tools that call models).

**Consequences.**
- `byok_keys` is a **core** table (already in `002_credentials.sql`), not deferred.
- The deferred A5 gateway design is absorbed into RFC-0007's "future" section.

---

## D3 — API token scopes: full access in v1

**Context.** `access_tokens` could support per-workspace or per-action scopes
(`workspace:read`, `publish`, …). Designing scopes now is speculative — there is
no multi-tenant abuse signal yet.

**Decision.**
- v1: a token grants **full access to all workspaces owned by the token's user**
  — equivalent to the user's own session.
- No scope column is shipped until a concrete abuse/least-privilege need appears.

**Consequences.**
- Token UI stays minimal (create / list prefix / revoke).
- Users are advised to rotate tokens per client (Cursor, CLI, …) so revocation is
  tractable in lieu of scopes.
- See [Future — token scopes](./FUTURE.md).

---

## D4 — Publish is always explicit (opt-in)

**Context.** Tools and agents can write drafts freely. Auto-publishing on write
would be convenient but creates abuse, cost, and surprise-visibility risk.

**Decision.**
- `publish` is a **distinct, explicit action** — a separate call/flag, never a
  side effect of writing a file.
- Tools declare `may_publish` in their spec; even then, publish requires an
  explicit `publish` argument from the caller.
- Public `/p/{id}` URLs are never created implicitly.

**Consequences.**
- "Draft then publish" is a hard invariant in the data flow.
- Agents that want one-shot publish must pass the publish flag explicitly.

---

## D5 — Secure share `/s/` is a designed hardening track item

**Context.** `password_hash` exists on `workspace_items` and `/s/{public_id}` is
referenced across docs, but there was no design for the session/cookie model.

**Decision.**
- Promote `/s/` to a real (short) RFC: **[RFC-0006](./rfc/0006-secure-share.md)**.
- Mechanism: password validates against `password_hash`; on success, a short-lived
  signed cookie grants streaming access from the **private** bucket — the file is
  never copied to the public bucket.
- `/s/` is **Track H5**, not MVP. MVP ships with public `/p/` only.

**Consequences.**
- `password_hash` is a core column (already present); the route + cookie logic is
  the only new build.
- Files shared via `/s/` are not CDN-cached (intentional — they are restricted).

---

## D6 — Abuse posture: universal sandbox + isolated content domain

**Context.** Hosting arbitrary user HTML is abuse-sensitive (phishing, malware,
CSRF). Crucially, **auth does not prevent phishing** — a registered attacker is as
dangerous as an anonymous one. The abuse problem is a function of hosting arbitrary
HTML on a domain you own, *not* of guest-vs-authenticated, so the controls must be
**universal** — applied to all published content.

**Decision.**
- **All** published HTML is served from a separate **content domain**
  (configurable via `PAGES_BASE_URL`; our hosted SaaS uses `bami.page`),
  never the app domain. Reputation isolation + origin isolation.
- **All** published responses carry this CSP, applied at the **CDN edge** (or via
  object metadata), with no app compute:
  `Content-Security-Policy: sandbox allow-scripts; connect-src 'none'; form-action 'none'`
  - `allow-scripts` → JS runs (GSAP/animations work — a product requirement).
  - No `allow-same-origin` / `allow-forms` / `allow-top-navigation` / `allow-popups`
    → opaque origin, no cookie/session theft, **no credential-phishing exfil**,
    no redirect, no popups. A page can *look* like a login but cannot transmit
    typed credentials.
- Day-one mandatory: per-IP + per-user **rate limits**, **size cap**, **3-day TTL**
  for anonymous (D8), **report/takedown** endpoint, **Safe Browsing scan** on
  publish.
- **Auth is a friction/traceability dial, not the abuse control** — it adds
  bannable identity + signup friction + per-user quotas on top of the universal
  sandbox.
- Accepted residual (JS on): visual-only scams that can't exfil; crypto miners
  (bounded by TTL + report + light miner-pattern sanitize).

**Consequences.**
- Rendering is **CDN → S3 direct** (zero FastAPI compute). If `PAGES_BASE_URL` is
  unset (self-host, same-origin `/p/{id}`), the CSP header is set by the app or a
  front-CDN instead — same policy, slightly less isolation.
- The app domain (`bamitools.com`) never serves rendered user HTML — only auth,
  claim, and API surfaces. Untrusted HTML lives on the content domain.
- H4 moderation builds on top of this baseline; it is not the primary defense.

---

## D7 — Status taxonomy (canonical)

**Context.** "Deferred", "later", "hardening", and "future" were used
interchangeably, making it unclear what has a design vs. what is a bullet.

**Decision.** Exactly four statuses, used everywhere in these docs:

| Status | Meaning | Documented in |
|---|---|---|
| **Active** | On the build path now | [TODO.md](./TODO.md) Tracks C / T; RFCs 0001–0003, 0006–0007 |
| **Hardening** | Named, thin spec; after/alongside MVP | [TODO.md](./TODO.md) Track H |
| **Deferred** | Full design exists; explicitly parked | RFCs 0004–0005; [TODO.md](./TODO.md) Track D |
| **Future** | Idea only; no design | [FUTURE.md](./FUTURE.md) |

**Consequences.**
- Anything not matching one of these four gets reclassified or designed.
- If a status is unclear, it defaults to **Future** until it gets an RFC.

---

## D8 — Storage quota for registered users; time-based expiry only for anonymous

**Context.** The original free-tier model used **inactivity TTL** — delete a
registered user's files if they don't log in for N days. This is hostile ("use it
or lose it"), breaks published links without warning, and is a worse free-tier
story than a storage cap. Meanwhile the anonymous/guest path (D1) genuinely needs
time-bounded storage, since unauthenticated throwaway use has no quota bearer.

**Decision.**
- **Registered users** are bounded by a **per-user storage quota**, never by
  inactivity:
  - Free: **1 GB**
  - BYOK: **5 GB** (the reward for bringing your own model key)
  - Paid: **50 GB+**, plus permanent public pages
- **Anonymous/guest** content (the trial path, per D1) gets a
  **3-day `expires_at`** and is auto-deleted by a cron. It is **reclaimable**: a
  user who signs up within the window moves the draft into their quota'd workspace
  via `reclaim_key`.
- Numbers are policy defaults, tunable; the mechanism (quota vs expiry) is the
  decision.

**Consequences.**
- `workspace_items.expires_at` is the expiry column for anonymous content; the
  H1 cron sweeps expired anonymous rows + enforces registered quotas on write.
- Registered content is safe across long absences — no surprise deletions.
- Cost is bounded on both axes: per-user (quota) and per-anonymous-upload (TTL).
- The numbers (1 / 5 / 50 GB) live in [TODO H1](./TODO.md), [introduction tiers](./introduction.md),
  and [RFC-0001 cost model](./rfc/0001-core-platform.md); update all three together.

---

## D9 — Configurable content domain + guest two-link mechanics

**Context.** D1 brings guest back into the MVP; D6 isolates all rendered HTML to a
separate content domain with a sandbox header. This decision pins the concrete
mechanics: the configurable domain, the two-link guest flow, and the CDN-direct
rendering path — while keeping self-hosting simple.

**Decision.**
- **Content domain is configurable** via the `PAGES_BASE_URL` env var
  (`.env.example` → `.env`):
  - **Empty (default)** → published URLs are relative `/p/{public_id}` on the app
    origin. Works for anyone, no extra domain. CSP header set by the app or a
    front-CDN.
  - **Set** (e.g. our hosted SaaS `https://bami.page`) → published URLs are
    `https://bami.page/{public_id}`; CDN → S3 direct; CSP header at the edge;
    full reputation/origin isolation from the app domain.
  - Self-hosters set their own domain or leave it empty.
- **Rendering path (when set):** viewer → `bami.page/{id}` → CDN (injects the D6
  CSP header) → S3 public bucket → viewer. **Zero app compute on views.**
- **Guest two-link output** (web paste or MCP guest mode):
  - **View link** `{PAGES_BASE_URL or /p}/{public_id}` — shareable; renders for
    anyone with the unguessable URL; sandboxed; 3-day TTL.
  - **Claim link** `{app origin}/claim?token={reclaim_key}` — private to the
    creator; app-served; looks up the draft by `reclaim_key`; log in (one click) →
    draft moves into the new account's workspace, key consumed.
  - First-claim among `reclaim_key` holders wins; only the creator holds it → no
    theft race. A view-link holder cannot claim (no `reclaim_key`).
- **Authenticated publish** (token MCP / logged-in web) skips the claim step and
  writes straight to the content URL — **still sandboxed per D6**, just no claim
  step and no 3-day TTL. Registered and guest pages are sandboxed **identically**.
- **Claim states:** valid+unclaimed → claim page; already-claimed → "claimed by
  its owner"; expired/invalid → "invalid or expired."

**Consequences.**
- `reclaim_key` must be **unique** (lookup key) — ensure a unique index.
- The view URL and claim URL share no identifier (`public_id` vs `reclaim_key`) →
  independent capabilities.
- MCP `publish` returns `{ view_url, claim_url? }` — `claim_url` present only in
  guest mode.
- The hosted product registers and sets `bami.page`; nothing in code hardcodes it.

---

## Changelog

| Date | Decision |
|---|---|
| 2026-07-12 | D1–D7 recorded; resolves guest/reclaim, BYOK ownership, scopes, publish, `/s/`, abuse posture, taxonomy |
| 2026-07-12 | D8 recorded: storage quota for registered (1/5/50 GB); 3-day expiry for anonymous only |
| 2026-07-12 | D1/D6 revised + D9 added: guest is the MVP trial funnel (view+claim links); universal sandbox on a configurable content domain (`PAGES_BASE_URL`, hosted = `bami.page`); auth = friction dial |
