# RFC-0003: Pluggable Tools

> **Status:** Draft · **Active** (design; implement after Core track C1–C7)  
> **Author:** Quan  
> **Created:** 2026-07-12  
> **Last Updated:** 2026-07-12  
> **Depends on:** [RFC-0001](./0001-core-platform.md), [RFC-0002](./0002-mcp-and-tokens.md)

---

## 1. Thesis

The platform owns **auth, workspaces, storage, and publish**.  
**Tools** are thin converters that:

```text
input → transform → write workspace file(s) → optional publish → return URLs
```

Adding a tool (PDF → HTML, article → HTML slides) must not reimplement identity or buckets. Register a handler, validate input, write outputs.

This is **not** the multi-agent LangGraph pipeline ([RFC-0004](./0004-deferred-langgraph-pipeline.md)). Prefer one LLM call, deterministic templates, or existing libraries. Use a graph only if a single tool truly needs it later.

---

## 2. Product fit

| Tool (example) | Input | Output artifact |
|---|---|---|
| `article-to-slides` | URL or pasted article text | HTML slide deck (`mode=html`) |
| `pdf-to-html` | PDF upload | Readable HTML page |
| `md-to-page` | Markdown | Clean reading page |
| `csv-to-table` | CSV | Static table page |

Brand line: **turn X into a shareable HTML page.**

Reject tools that do not produce a workspace artifact or public URL.

---

## 3. Tool contract

### 3.1 Spec

```text
ToolSpec:
  id: str                    # e.g. "article-to-slides"
  title: str
  description: str
  input: multipart | json | url
  auth: required             # user session or API token
  runs: sync | async         # async only when wall time >> 2s
  writes: list[path]         # workspace paths produced
  may_publish: bool
  returns: {
    item_paths: list[str],
    public_url: str | null
  }
```

### 3.2 HTTP API (sketch)

```
POST /api/tools/{tool_id}
Authorization: Bearer … | session
Content-Type: application/json | multipart

→ 200 { item_paths, public_url? }
→ 202 { job_id }   # if async
```

`GET /api/jobs/{job_id}` when async is introduced.

### 3.3 MCP (later)

```
run_tool(tool_id, args) → same return shape
```

Or tool-specific MCP tools that wrap the registry.

---

## 4. Registry layout

```text
bamitools_server/tools/
  registry.py              # id → ToolSpec + handler
  base.py                  # Protocol / ABC
  article_to_slides/
    handler.py             # pure transform + write via platform services
    schema.py              # Pydantic input
  pdf_to_html/
    handler.py
    schema.py
```

**Rule:** Handlers receive a `ToolContext` with `user_id`, `workspace_id`, and helpers:

- `write_item(path, content, mode=…)`
- `publish(path) → public_url`
- `usage_log(action, meta)`

Handlers must not open raw S3 clients or bypass authz.

---

## 5. Sync vs async

| Mode | When |
|---|---|
| **Sync** | Default; article→slides, small markdown |
| **Async (arq)** | Large PDF, long OCR, multi-minute jobs |

Do not build a general job queue until the first tool needs it. Platform may share a queue later with deferred pipeline (RFC-0004).

---

## 6. Example tools (sketches)

### 6.1 `article-to-slides` (recommended first tool)

1. Accept `url` or `text`.
2. If URL: fetch + extract main content (readable subset).
3. Structure into sections (rules or one LLM call with structured output).
4. Render HTML slide deck (template or simple CSS full-page sections).
5. `write_item("slides/{slug}.html", html, mode="html")`.
6. Optional `publish` → `/p/{id}`.

### 6.2 `pdf-to-html` (second)

1. Accept PDF multipart; size limit.
2. Extract text (and images if needed) via library.
3. Emit semantic HTML; store PDF as `raw` sibling optional.
4. Write `mode=html`; optional publish.

Heavier deps and layout quality issues — ship after slides.

---

## 7. Auth, quota, cost

- All tools require authentication (session or API token).
- Count toward per-user rate limits and `usage_log`.
- If a tool calls an LLM: use platform key (metered) or user BYOK (`byok_keys`).
- Free tier: hard caps; paid/BYOK: higher or unlimited.

---

## 8. Security

- Validate and cap input size.
- HTML output: escape untrusted strings; CSP on published pages.
- URL fetch: SSRF protections (block private IPs, timeouts).
- PDF: virus-scan optional later; reject huge files early.

---

## 9. Explicit non-goals

- Shared multi-agent “kitchen” for all inputs → RFC-0004  
- Chat as tool orchestrator → RFC-0005  
- Community widget marketplace (premature)

---

## 10. Implementation order

1. Core track complete (auth, workspace I/O, publish, tokens).  
2. Registry + one sync tool (`article-to-slides`).  
3. Optional MCP `run_tool`.  
4. `pdf-to-html` + async if required.  

---

## 11. Open questions

1. Versioning tool IDs (`article-to-slides@2`) vs breaking changes in place.  
2. Storing tool inputs as `raw` items for re-run.  
3. Whether publish is always opt-in (recommended: yes).  
