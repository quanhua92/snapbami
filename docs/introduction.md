# SnapBami

Paste raw text → get a shareable dashboard in seconds.

## What is it

SnapBami is a visual pastebin for data. You paste unstructured text — numbers, metrics, status updates — and AI structures it into a clean, interactive dashboard with KPI cards, charts, and tables. Each dashboard gets a permanent share link and embeddable iframe, served as static files from S3.

## The problem

You have data. You want to share it visually. Your options today:

- **Notion/Google Sheets** — 30 minutes of manual chart building
- **Tableau/Power BI** — requires a database, account, and training
- **ChartGen.ai** — requires formatted CSV upload, no instant share
- **GitHub Gist** — text only, no visual widgets
- **Twitter/Slack** — screenshots, no interactivity

None of these let you paste raw text and get a shareable dashboard instantly.

## The gap we fill

> **"I have text, I want a pretty shareable page, instantly."**

No signup required. No CSV upload. No manual layout. Paste → publish → share.

## Two modes

| | AI Mode | Manual Mode |
|---|---|---|
| Input | Any raw text | Template form or markdown |
| Login | Required | **Not required** |
| Cost | ~$0.002 per dashboard | **$0** |
| Latency | 3–5 seconds | **<500ms** |
| Best for | Messy, unstructured input | Already-formatted data from ChatGPT/Claude |

## How it works

**Create:** You POST text → FastAPI runs a multi-agent LangGraph pipeline (or deterministic template parser) → uploads static JSON + HTML to S3.

**Read:** Viewers fetch directly from S3 via Cloudflare CDN. **The server is never involved.** $0 per view, scales infinitely.

## Why it's different

| vs Competitor | SnapBami advantage |
|---|---|
| ChartGen.ai | Raw text input (not CSV). Instant share link. Embed iframe. |
| Notion | AI structures it for you. No manual layout. |
| Tableau Public | Zero learning curve. No account. Pastebin fast. |
| GitHub Gist | Visual widgets + charts, not just text. |

## Technical highlights

- **$0 read path** — all dashboards are static files on S3, served via Cloudflare cache
- **Real multi-agent pipeline** — LangGraph with extractor → router → writers → editor
- **Guardrail gate** — blocks prompt injection, PII, XSS before any LLM call
- **Anonymous reclaim** — 7-day TTL, claim by signing up to keep permanently
- **MCP integration** — create dashboards from Cursor/Claude Desktop

## Tech stack

FastAPI · LangGraph · OpenAI-compatible LLM · Firebase Auth · Onidel S3 · Redis · PostgreSQL · Docker

## Who uses it

- Indie hackers sharing monthly metrics
- Developers sharing benchmark results
- Job seekers showing portfolio stats
- Teams posting weekly status updates
- Students sharing project data

## Cost

| Action | Cost |
|---|---|
| AI mode create | ~$0.002 |
| Manual mode create | $0 |
| View any dashboard | $0 |
| Store on S3 | ~$0 (within Onidel 2TB) |
