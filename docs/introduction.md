# SnapBami

> **The rendering layer local AI has been missing.**

ChatGPT has Canvas. Claude has Artifacts. Your local model has terminal output.

SnapBami gives any AI — local or cloud — the ability to publish interactive HTML via one API call. Get a shareable, embeddable URL instantly.

---

## The problem

AI models generate rich output every day — benchmarks, metrics, comparisons, charts. But where does it go?

> **ChatGPT Canvas / Claude Artifacts** — render in-chat and can be shared via links. But you can't embed them in your own pages, control their lifecycle, or use them with a different AI provider. Locked to one platform, one subscription.

> **Local models (Ollama, DeepSeek, Llama)** — generate great code and analysis, but have no built-in way to publish, share, or embed visual output. Some UIs render HTML locally, but there's no shareable URL.

> **Every AI tool** — produces visual data that's hard to persist, embed, or share outside the platform that created it.

---

## MCP tools

| Tool | Input | Output |
|---|---|---|
| `list_widgets` | *(optional)* author, tag | Curated widgets with descriptions and examples |
| `read_widget` | Widget ID | Full widget content (HTML + CSS + manifest) |
| `publish_page` | Widget layout or raw HTML | Shareable URL |
| `update_page` | Dashboard ID + new content | Same URL, updated content |

Browse curated widgets, read their source, publish, update. Four tools.

---

## How SnapBami compares

| | ChatGPT Canvas | Claude Artifacts | Local Models | **SnapBami** |
|---|:---:|:---:|:---:|:---:|
| Render visual output | Yes | Yes | Limited | **Yes** |
| Shareable via URL | Yes | Yes | No | **Yes** |
| Embeddable (Notion/Slack/docs) | No | No | No | **Yes** |
| Works with any AI | OpenAI only | Anthropic only | — | **Yes** |
| BYOK (your own key) | No | No | Yes | **Yes** |
| No subscription required | No | No | Yes | **Yes** |
| Structured widget system | No | No | No | **Yes** |
| API/MCP for programmatic creation | No | No | No | **Yes** |

---

## How it works

Two creation paths — same output (static HTML, shareable URL):

### 1. AI publishes

External AI (Cursor, Claude, Copilot) generates widgets or raw HTML via MCP/API. SnapBami just hosts. **The AI is the creator.**

### 2. SnapBami creates

User provides data. SnapBami's own multi-agent pipeline (LangGraph: extractor → router → writers → editor) processes it into widgets → renders HTML. *Like NotebookLM: give it data, get a visualization.*

Input methods (all supported, rate-limited by resource cost):

| Input | Cost | Rate limit |
|---|---|---|
| **Text paste** (raw text, CSV, JSON, markdown) | Cheap | High |
| **URL fetch** (SnapBami fetches + extracts) | Moderate | Medium |
| **PDF/Images** (OCR extraction) | Expensive | Low |
| **BYOK** (register your own API key) | User pays | **None** |

> **Read path:** Viewers fetch directly from S3 via Cloudflare CDN. **The server is never involved.** $0 per view, scales infinitely.

---

## The widget architecture

### Composable widgets

Widgets are self-contained HTML/CSS/JS components — each designed by powerful models (Opus, GPT-4) for maximum quality. They live in a curated, versioned library:

```
widgets/
├── kpi-card/         # metric + change indicator
├── bar-chart/        # categorical comparison
├── line-chart/       # time series
├── table/            # tabular data
├── progress-tracker/ # goal progress
├── status-feed/      # list of updates
└── ...               # community widgets
```

### SSG rendering (no client JS)

At **create time**, the server renders the JSON spec into a complete, self-contained HTML page. Viewers get a fully baked page that works without JavaScript.

```
Create time (server):
  JSON spec + widget templates (Jinja2)
    → rendered into complete static HTML → uploaded to S3

View time (browser):
  GET /d/{id} → fully rendered HTML, no JS required
```

> **Templates** are pre-built JSON specs — guided setups with widgets already arranged.
> Start from a template, change the data, server re-renders.

The JSON spec (`d/{id}.json`) is stored alongside for edits and updates only — **viewers never need it.**

### Per-widget: guided or raw

Each widget slot can independently be guided or raw — mix freely. The root HTML (page shell: grid, theme, header) is also customizable.

```json
{
  "title": "Q4 Results",
  "root_html": "<optional custom page shell>",
  "layout": [
    {"type": "guided", "widget_id": "kpi-card", "props": {"label": "Revenue", "value": "$4.2k"}},
    {"type": "raw", "html": "<canvas>custom d3 viz</canvas>"},
    {"type": "guided", "widget_id": "kpi-card", "props": {"label": "Users", "value": "1200"}}
  ]
}
```

| Mode | How | Best for |
|---|---|---|
| **Guided** | widget id + props → server renders from template | 80% of slots. Cheapest. |
| **Raw** | completely custom HTML in that slot | Unique visualizations. Unlimited. |

Omit `root_html` → default shell. Provide it → AI's custom theme, layout, fonts, animations.

### Widget manifests

Each widget ships with a **manifest** — a JSON guide the cheap model reads to understand what's available, when to use it, and what data to extract:

```json
{
  "id": "kpi-card",
  "description": "Single metric with change indicator. Use for standalone numbers.",
  "best_for": ["headline metrics", "before/after comparisons"],
  "props": {
    "label": {"type": "string", "required": true, "description": "Metric name"},
    "value": {"type": "string", "required": true, "description": "Display value"},
    "change": {"type": "string", "description": "Delta, e.g. '+15%'"},
    "trend": {"type": "enum", "values": ["up", "down", "flat"]}
  },
  "examples": [
    {"label": "Revenue", "value": "$4.2k", "change": "+15%", "trend": "up"}
  ]
}
```

> The manifest **IS the prompt** for the cheap model. No guessing — it knows exactly what widgets exist, what they do, and how to fill them.

---

## BYOK + free tier

| Tier | LLM | Rate limit | Storage | Who |
|---|---|---|---|---|
| Anonymous | SnapBami's DeepSeek V4 *(free)* | Per IP | 3 days inactive | Try without signup |
| Registered *(free)* | SnapBami's DeepSeek V4 *(free)* | Per IP | 30 days inactive | Regular use |
| Registered *(BYOK)* | User's own key *(any provider)* | **None** | 30 days inactive | Power users |
| Paid | Any | None | **Permanent** | Permanent embeds |

> Dashboards expire based on **inactivity**, not creation date. Every view resets the timer — popular content stays alive, abandoned content auto-expires.

> Register your own API key to bypass rate limits entirely — you pay your own LLM costs.

---

## MCP-first

Any MCP-compatible AI tool can create and embed content:

```
User: "Benchmark 3 JSON parsers, show results"

Cursor: [creates SnapBami dashboard via MCP tool]
         → Returns embedded interactive HTML in chat
         → Link persists for sharing
```

**MCP tools:** `list_widgets` · `read_widget` · `publish_page` · `update_page`

---

## Why it's different

| vs Competitor | SnapBami advantage |
|---|---|
| ChatGPT Canvas / Claude Artifacts | **Embeddable.** Any AI, not just one provider. BYOK, no subscription. API/MCP for programmatic creation. |
| ChartGen.ai | AI generates the layout. Any input, not just CSV. MCP integration. |
| Notion | Instant. No manual layout. Embeddable anywhere. |
| GitHub Gist | Interactive widgets + charts, not just text. |
| Plain LLM chat | Output persists. Shareable. Embeddable. Not lost in scroll. |

---

## Tech stack

**FastAPI** · LangGraph · OpenAI-compatible LLM (BYOK) · RustFS/S3 · Redis · PostgreSQL · Docker · MCP

## Security

- Each dashboard is an isolated static HTML page (sandboxed iframe for embeds)
- No access to SnapBami's API, cookies, or auth tokens
- Guardrail gate: size limits, input validation, rate limiting
- Content-Security-Policy restricts external requests

## Cost

| Action | Cost |
|---|---|
| AI create *(free tier)* | SnapBami pays (~$0.0001, DeepSeek V4, rate-limited) |
| AI create *(BYOK)* | User's LLM cost *(any provider)* |
| Raw HTML create | $0 |
| View any dashboard | $0 |
| Store on S3 | ~$0 *(auto-expired per tier)* |
