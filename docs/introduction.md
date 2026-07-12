# BamiTools

Most AI output never leaves the chat where it was made. Vendor links expire, you can't embed freely or own the lifecycle, and local models have no shareable URL at all.

BamiTools gives that output a home you own: an **authenticated workspace** for private drafts, and a **durable public URL** (`/p/{id}`) for finished HTML. Reach it from the web UI, a REST API, or MCP from any AI agent — Cursor, Claude Desktop, your own scripts. Add small converter tools later (article→slides, PDF→page) without rebuilding anything.

**One line:** authenticated workspace for private files and published HTML — web, API, or MCP; add tools when you need them.

> The rest of these docs sometimes uses a bánh mì-shop metaphor (workspace = shelf, published file = bánh mì). It's flavor, not a prerequisite — full vocabulary in [metaphor.md](./metaphor.md).

---

## The problem

AI models generate rich output every day — notes, benchmarks, charts, decks. But where does it go? Most of it never leaves the kitchen counter of a single chat vendor.

> **ChatGPT Canvas / Claude Artifacts** — great in-chat; shareable links exist, but you rarely own lifecycle, embed freely, or use the same artifact flow with a different AI.

> **Local models (Ollama, DeepSeek, Llama)** — strong cooks, no storefront: no built-in shareable URL.

> **Every AI tool** — produces something worth handing over, but it is hard to **stage privately**, **publish cleanly**, and **keep** outside the platform that made it.

BamiTools answers: **put it on your shelf; when ready, put it in the glass case.**

---

## What this product will become

Not another chatbot. Not a generic cloud drive. Not a full “build any app” site builder.

**The end state:** the layer between AI tools and the open web — a shelf you own, bánh mì (HTML pages, decks, reports) you can link or embed, and a simple way to bolt on “make HTML from X” stations without changing the shop.

### Three layers of the shop

```text
┌──────────────────────────────────────────────┐
│  Specialty stations (tools — later)          │
│  article→slides, PDF→HTML, …                 │
│  thin converters; same shelf + publish       │
├──────────────────────────────────────────────┤
│  Guest cooks (agents — MCP + API tokens)     │
│  Cursor / Claude Desktop / scripts           │
│  list · read · write · publish               │
├──────────────────────────────────────────────┤
│  The shop (platform core)                    │
│  Auth (who owns the shelf)                   │
│  Workspace · private files · publish         │
│  Back shelf /w/…  →  front case /p/{id}      │
└──────────────────────────────────────────────┘
```

Everything valuable ends the same way: **a file on the shelf**, optionally **a public bánh mì** people can open or embed.

### Day in the life

| Who | What happens |
|---|---|
| **You** | Sign in → open your shelf → drop or generate files → **publish** → hand someone `/p/{id}`. That link is the product moment. |
| **Your AI (Cursor, …)** | API token + MCP: writes `notes/spec.html` or `decks/q3.html`, publishes when you say so. Same shelf — not a vendor-only sandbox. |
| **A tool (later)** | “Paste article → slides,” “PDF → readable HTML.” The station does not invent hosting; it leaves a bánh mì on *your* shelf and may put it in the case. |

### Who it is for (over time)

| When | Customer |
|---|---|
| **Now (MVP)** | Builders in Cursor/Claude who want a link they own — private drafts, then publish — without ChatGPT/Claude lock-in. |
| **Next** | People who want one-click converters (article → deck, PDF → page) on the same account and URLs, without learning MCP. |
| **Later (if sticky)** | Teams, permanent embeds, custom domains; chat/Telegram as *extra doors* into the same shelf — not a new product identity. |

### What success looks like

| Milestone | Meaning |
|---|---|
| **MVP** | You (and a few others) weekly write or have an agent write a file, publish, and send `/p/{id}` — and it still matters days later. |
| **Product** | BamiTools is the default place finished HTML goes — like Gist for snippets, but for **pages / decks / reports**, with private staging and clean public URLs. |
| **Business (optional)** | Paid tier for **permanent** public pages and larger storage (50 GB+); free tier capped at 1 GB (never deleted for inactivity); BYOK so tool LLM cost is not the host’s problem. Views stay cheap (CDN static). |

### What it is not

| Tempting path | Why not (v1) |
|---|---|
| Full Claude-like chat as the app | Competes with frontier chat UIs; chat is a later channel ([RFC-0005](./rfc/0005-deferred-chat-telegram.md)) |
| One giant multi-agent “any dashboard” kitchen | Slow, expensive, quality-hard; open with small stations first ([RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md) is deferred) |
| Generic cloud drive | A shelf with no **display case** is just storage |
| Hosted app builders (v0 / Lovable-style) | We sell **owned HTML artifacts from workflows**, not full product apps |

The workspace is **never** the bánh mì. The shelf holds ingredients and finished dishes; only files — especially published HTML — are the sandwich.

### Example bánh mì

1. **Research note** — Agent writes `research/competitor.html` → publish → share with a cofounder.  
2. **Slide dump** — Paste a long article → tool produces a deck → present from `/p/…`.  
3. **PDF handoff** — Client PDF → readable HTML; later password case `/s/…`.  
4. **Local model path** — Ollama helps write HTML on your machine; MCP/API puts it on the shelf and in the case so others open it without your laptop.

Same spine every time: **identity → file → optional tool → publish → URL**.

### Roadmap as the shop grows

| Phase | Product becomes… |
|---|---|
| **Core (Track C)** | “My authenticated shelf + publish URL + agent access” |
| **Tools (Track T)** | “I don’t always need Cursor — one-click X→HTML still lands on my shelf” |
| **Hardening (Track H)** | Trust: rate limits, CSP, moderation, nicer counter UI, secure shares |
| **Deferred chat / Telegram** | Mobile and paste channels into the *same* shelf |
| **Deferred LangGraph kitchen** | Only if simple stations cannot do a complex multi-step job |

Build tracker: [TODO.md](./TODO.md).

---

## What BamiTools is (v1)

| Layer | Shop role | Product role |
|---|---|---|
| **Auth** | Customer account — who owns the shelf | Sign-in → internal user id; API tokens for agents |
| **Workspace** | Back shelf | Private files (`/w/{workspace_id}/…`) |
| **Publish** | Move to front display case | Public CDN HTML (`/p/{public_id}`) |
| **MCP** | Wholesale / guest cook line | list / read / write / publish from Cursor, Claude Desktop, etc. |

**Not v1:** multi-agent LangGraph kitchen crew, chat-as-primary counter, Telegram takeout. Designs live in deferred RFCs.

---

## How it works

### Shelf and display case (storage)

| Space | Metaphor | Detail |
|---|---|---|
| **Private workspace** | Back shelf | `/w/{workspace_id}/{filepath}` → `s3://bamitools-private/…` · session JWT or API token · owner-only |
| **Public pages** | Front glass case | `/p/{public_id}` → `s3://bamitools-public/…` · public · CDN · **~$0 app compute** on views |
| **Secure share (later)** | Off-menu / regulars-only | `/s/{public_id}` · password before streaming from private storage |

### Ingredients vs dishes

| `mode` | Metaphor | Meaning |
|---|---|---|
| `raw` | Ingredient | Upload, paste, source PDF/CSV/MD |
| `html` | Bánh mì, wrapped | Finished HTML page or deck |
| `pipeline` | Reserved kitchen line | Deferred multi-agent output ([RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md)) |

A raw CSV on the shelf is flour. The same data as HTML is a sandwich ready for the case.

### MCP tools (guest cooks)

| Tool | Input | Output |
|---|---|---|
| `list_workspace_files` | optional directory | What’s on the shelf |
| `read_workspace_file` | path | Content |
| `write_workspace_file` | path, content | Draft on the back shelf |
| `publish_item` | path | Bánh mì in the case: `/p/{public_id}` |

Details: [RFC-0002](./rfc/0002-mcp-and-tokens.md).

### Specialty stations (after core)

Small converters plug into the same write/publish path — no platform rewrite:

| Station | In → out |
|---|---|
| Article → slides | URL or text → HTML deck URL |
| PDF → HTML | PDF → readable page URL |
| Markdown → page | MD → clean reading page |

Contract: [RFC-0003](./rfc/0003-pluggable-tools.md).

---

## How BamiTools compares

| | ChatGPT Canvas | Claude Artifacts | Local models | **BamiTools** |
|---|:---:|:---:|:---:|:---:|
| Shareable URL | Yes | Yes | No | **Yes** |
| Embeddable / owned lifecycle | Limited | Limited | No | **Yes** |
| Works with any AI (MCP/API) | OpenAI only | Anthropic only | — | **Yes** |
| Private workspace FS (shelf) | No | No | Local only | **Yes** |
| BYOK later (bring your own sauce) | No | No | Yes | **Yes** |
| No single-vendor chat lock-in | No | No | Yes | **Yes** |

---

## Tiers (sketch)

| Tier | LLM (when stations need it) | Rate limit | Storage |
|---|---|---|---|
| Registered free | Platform key (metered) | Per user | 1 GB |
| Registered + [BYOK](./rfc/0007-byok.md) | User key | Higher / none | 5 GB |
| Paid | Any | Higher / none | 50 GB+ · permanent pages |

Registered content is **never deleted for inactivity** — only bounded by the quota.
**Guest** (no signup) is the zero-friction trial: paste or agent-publish → get a **view link** (3-day expiry, sandboxed) + a **claim link** (log in to own it). See [D1](./DECISIONS.md), [D6](./DECISIONS.md), [D9](./DECISIONS.md).

---

## Tech stack

**FastAPI** · PostgreSQL · Redis · S3-compatible storage · Docker · MCP · React SPA  

Deferred full kitchen / takeout: LangGraph pipeline, Telegram — [RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md), [RFC-0005](./rfc/0005-deferred-chat-telegram.md).

---

## Security

- Back shelf (`/w/`) requires owner auth.
- Front case (`/p/` / `bami.page`) serves **all** published HTML — registered and guest **identically** — under a strict CSP `sandbox` (JS runs for animations; no forms/connect/top-nav/popups). See [D6](./DECISIONS.md).
- Sanitize platform-generated HTML; treat raw uploads as untrusted ingredients.
- API tokens hashed at rest; never logged in full.

---

## Docs map

| Doc | Purpose |
|---|---|
| [metaphor.md](./metaphor.md) | Full bánh mì vocabulary |
| [DECISIONS.md](./DECISIONS.md) | Resolved policy (auth-first, BYOK, scopes, publish, `/s/`, abuse) |
| [RFC-0001](./rfc/0001-core-platform.md) | Auth, workspaces, storage, publish (**active**) |
| [RFC-0002](./rfc/0002-mcp-and-tokens.md) | API tokens + MCP (**active**) |
| [RFC-0003](./rfc/0003-pluggable-tools.md) | Specialty stations / tool runner (**active design**) |
| [RFC-0006](./rfc/0006-secure-share.md) | Secure share `/s/` (**hardening, Track H5**) |
| [RFC-0007](./rfc/0007-byok.md) | Bring-your-own-key (**active, Track T prerequisite**) |
| [RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md) | Multi-agent kitchen (**deferred**) |
| [RFC-0005](./rfc/0005-deferred-chat-telegram.md) | Chat counter + Telegram takeout (**deferred**) |
| [db.md](./db.md) | Schema guide |
| [TODO.md](./TODO.md) | Build tracker (Tracks C / T / H / D) + status taxonomy |
| [FUTURE.md](./FUTURE.md) | Idea-stage items with no design (teams, domains, billing, …) |

### Status of everything

One taxonomy — **Active / Hardening / Deferred / Future** — see
[DECISIONS.md D7](./DECISIONS.md) and the top of [TODO.md](./TODO.md).

### Later (not core)

- Multi-agent data → dashboard kitchen ([RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md))
- Web chat + Telegram ([RFC-0005](./rfc/0005-deferred-chat-telegram.md))
- Teams, custom domains, billing, and other idea-stage items ([FUTURE.md](./FUTURE.md))
