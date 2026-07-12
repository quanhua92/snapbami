# The Bánh Mì Metaphor

> The vocabulary we use to describe BamiTools, so every doc, pitch, and PR talks about the system the same way.

## One sentence

**Your workspace is the shelf. You and your AI are cooks. Each published file is a bánh mì — assembled, wrapped, and ready to hand to anyone.**

## Core mapping

| Bánh mì shop | BamiTools | Notes |
|---|---|---|
| **The bánh mì** | A created file / HTML artifact | The unit of value — note, deck, page, chart. |
| **The shelf** | Workspace (`/w/{workspace_id}/`) | Storage, *not* the product. Holds ingredients and finished dishes. |
| **Front display case** | Public pages (`/p/{public_id}`, or `bami.page/{id}` when `PAGES_BASE_URL` is set) | Moved from back shelf to glass case; served via CDN. |
| **Back shelf** | Private bucket (`bamitools-private`) | Drafts; token- or session-authorized only. |
| **Off-menu / regulars-only** | Secure share (`/s/{public_id}`) | Password-unlocked handoff. |
| **Customer account** | Auth (`users` + API tokens) | Who owns the shelf; required for v1 tools and agents. |

## Ingredients vs. dishes

Not every file is a finished bánh mì. `workspace_items.mode` marks the difference:

| `mode` | What it is | Metaphor |
|---|---|---|
| `'raw'` | Upload, paste, source PDF/CSV/MD | **Ingredient** — not yet food |
| `'html'` | Finished HTML page or deck | **Bánh mì, wrapped** — ready to serve |
| `'pipeline'` | Reserved (deferred multi-agent output) | Future kitchen line — see RFC-0004 |

A raw CSV on the shelf is an ingredient. The same data turned into HTML (by you, MCP, or a tool) becomes a bánh mì.

## The kitchen (v1)

| Bánh mì shop | BamiTools |
|---|---|
| **Specialty stations** | **Pluggable tools** — pdf→html, article→slides ([RFC-0003](./rfc/0003-pluggable-tools.md)) |
| **Guest cook / wholesale** | **MCP** — Cursor/Claude stocks the shelf ([RFC-0002](./rfc/0002-mcp-and-tokens.md)) |
| **Assemble + wrap + hand over** | **`publish`** — copy/render to public bucket → CDN |
| **Bring your own sauce** | **BYOK** — your LLM key for tools that need models |

The multi-agent “full kitchen crew” (LangGraph extractor/writers/editor) is a **deferred** expansion of the kitchen, not the shop’s opening menu ([RFC-0004](./rfc/0004-deferred-langgraph-pipeline.md)).

## The counter & channels

| Bánh mì shop | BamiTools (v1) |
|---|---|
| **Order counter** | Web workspace UI + REST API |
| **Call-ahead / wholesale line** | MCP + API tokens |
| **Takeout app (later)** | Telegram bot — deferred ([RFC-0005](./rfc/0005-deferred-chat-telegram.md)) |
| **Chatty waiter (later)** | In-app chat assistant — deferred; **not** the primary interface for v1 |

**Guest walk-in stool** = the zero-friction trial funnel — anonymous paste gets a **view link** + a **claim link**; sign up (one click) to own it. Authenticated seats are the durable path. See [DECISIONS.md D1](./DECISIONS.md), [D9](./DECISIONS.md).

## Why this metaphor (and not another)

A bánh mì is a **single, finished, made-once, handed-over item.** That shape maps onto a file. It does *not* map onto:

- A living, tended, evolving space (that's a **garden** — wrong shape).
- A loose pile of utilities with no shelf (that's only the `-tools` suffix talking).

So: the workspace is *never* the bánh mì. It's the shelf. Only files (especially published HTML) are bánh mì. Auth is who owns the shelf.

When the metaphor gets in the way of clarity, drop it and use the plain term. The metaphor is a vocabulary aid, not a cage.
