# RFC-0004: Deferred — Multi-Agent Pipeline (LangGraph)

> **Status:** Deferred  
> **Author:** Quan  
> **Created:** 2026-07-11 (content from former RFC-0001)  
> **Last Updated:** 2026-07-12  
> **Depends on:** RFC-0001 (core platform), RFC-0003 (pluggable tools)  
> **Supersedes section of:** former `0001-bamitools-ai-system.md` (pipeline / widgets / gateway)

---

## Deferral notice

**Not on the critical path.** Do not implement until pluggable tools ([RFC-0003](./0003-pluggable-tools.md)) prove insufficient for a specific use case.

Active product surface is **auth + workspaces + publish** ([RFC-0001](./0001-core-platform.md)), then thin tools. This document preserves the multi-agent design so the work is not lost.

BYOK / model-gateway detail moved to [RFC-0007](./0007-byok.md).

---

## 1. Thesis (deferred)

BamiTools' own multi-agent pipeline turns raw input (text/CSV/URL/PDF) into layout files inside a workspace via LangGraph, then optional publish to `/p/{id}`.

This is a **second creation path** after external agents (MCP) and simple tools. It is not required for MVP.

---

## 2. Request Lifecycle

```
User / Agent submits data (text/CSV/URL/PDF)
  │
  ▼
┌──────────────────┐
│  API Gateway     │  Auth checks (Bearer token / session) & routing
│  ~2ms            │
└──────┬───────────┘
       ▼
┌──────────────────┐
│  Guardrail Gate  │  Size check → PII scan → injection screen → dedup hash
│  ~5ms            │
└──────┬───────────┘
       ▼
┌──────────────────┐
│  LLM Cache Check │  Redis lookup by content hash
│  ~1ms            │
└──────┬───────────┘
       │ miss
       ▼
┌──────────────────┐
│  Job Queue       │  arq enqueues pipeline job → returns job_id
│  ~5ms            │  Client polls /api/jobs/{job_id} or receives webhook
└──────┬───────────┘
       ▼
┌──────────────────┐
│  LangGraph       │  Extractor → Router → Writers (parallel) → Editor
│  Pipeline        │  ~3-8s wall time, 4-7 LLM calls
│  (worker)        │
└──────┬───────────┘
       ▼
┌──────────────────┐
│  Render + Upload │  Jinja2 SSG → static files → S3 upload to private bucket
│  ~200ms          │  s3://bamitools-private/{workspace_id}/{filepath}
└──────┬───────────┘
       ▼
┌──────────────────┐
│  Record + Respond│  Postgres INSERT to workspace_items + private URL ready
│  ~10ms           │  Returns /w/{workspace_id}/{filepath}
└──────┬───────────┘
       ▼
┌──────────────────┐
│  Publish Action  │  User/Agent deploys private draft to public space
│  (Optional)      │  S3 Copy to public bucket {public_id} → Served via CDN
└──────────────────┘
```

**Latency budget:** Gate(~7ms) + Cache(~1ms) + Queue(~5ms) + Pipeline(~3-8s) + Render(~200ms) + DB(~10ms) = **3-8s total wall time.** Not real-time — this is a generation task. User sees a loading state; result persists.

---

## 3. Multi-Agent Pipeline (LangGraph)

### 3.1 Why LangGraph

- **Tradeoff considered:** Raw chain of LLM calls (simpler, no graph overhead) vs LangGraph (graph orchestration, parallel fan-out, state management, checkpointing).
- **Tiebreaker:** The pipeline has **parallel fan-out** (multiple writers run concurrently) and **conditional routing** (router decides which writers to activate). LangGraph's `Send` API and `Annotated[list, operator.add]` reducer handle this natively.
- **Principle:** Use a framework when the control flow it models matches your problem. Fan-out + conditional routing IS a graph.

### 3.2 Pipeline state

```python
class PipelineState(TypedDict):
    raw_text: str                           # input
    source_type: str                        # "text" | "csv" | "url" | "pdf"
    workspace_id: str                       # target workspace
    filepath: str                           # target path (e.g., 'notes/todo.md')
    entities: list[dict]                    # extractor output
    widgets: Annotated[list[dict], operator.add]  # reducer: writers accumulate
    final_spec: dict | None                 # editor output (validated JSON spec)
    errors: Annotated[list[str], operator.add]
    meta: dict                              # timing, model used, token counts
```

### 3.3 Node: Extractor

**Job:** One LLM call. Parse raw input into typed entities.

**Model:** Small tier (DeepSeek V4 / Haiku-class). This is extraction — structured output, no reasoning needed.

**Structured output:** `llm.with_structured_output(ExtractorResponse)` — Pydantic schema, no JSON parsing.

### 3.4 Node: Router

**Job:** Code only (no LLM). Map entity types to writer nodes.

The router filters entities, groups by writer type, and fans out via LangGraph `Send` messages. Each writer receives only its entities.

**Why code, not LLM:** Routing is deterministic. An LLM call here wastes 400ms and introduces non-determinism for zero value. **Principle: don't use an LLM where an if-statement works.**

### 3.5 Nodes: Writers (parallel)

Each writer is an LLM call that converts entities into widget specs.

**Parallel execution:** All activated writers run concurrently via LangGraph's parallel node execution.

**Reducer:** `Annotated[list, operator.add]` — each writer returns `{"widgets": [...]}`, the reducer concatenates all widget lists into `state.widgets`.

### 3.6 Node: Editor

**Job:** One LLM call. Validate, fix, and finalize the widget spec.

Responsibility: layout assignment, XSS escaping, title generation, quality check, and width validation.

**Model:** Mid tier (Sonnet-class). This is the quality gate — worth one good call.

### 3.7 Checkpointing

LangGraph checkpointing to Postgres — if the pipeline crashes mid-run (e.g., editor LLM call times out), the extractor + writer results are persisted. Resume only reruns the failed node.

### 3.8 Hallucination Prevention

**Defense stack (3 layers):**

1. **Extraction grounding (prompt-level):** Extractor prompt enforces "extract ONLY from the provided text."
2. **Entity validation (code-level):** After extraction, numbers and labels are matched against the raw text via regex. Non-verifiable entities are dropped.
3. **Post-generation audit (async):** Sampled pages are audited by an LLM-as-judge comparing values against the source text.

---

## 4. Execution Model

### 4.1 Sync vs Async

**Decision: Asynchronous via job queue.** The HTTP request returns a `job_id` immediately. The client polls `GET /api/jobs/{job_id}` or receives a webhook callback.

* **Tradeoff considered:** Synchronous (simpler client, one request) vs async (more complex, non-blocking).
* **Tiebreaker:** The pipeline takes 3-8s. Async enqueues free the HTTP connection, permitting high concurrency and enabling retries, backpressure, and job prioritization.

---

## 5. Widget System

### 5.1 Two assembly modes

- **Guided:** Spec only. Cheap model extracts fields into a pre-defined widget.
- **Raw:** Raw HTML/JS. Agent writes custom canvas or code directly.

### 5.2 Widget library

Pre-designed widgets (`kpi-card`, `line-chart`, `table`) are saved with HTML/CSS templates and manifests.

### 5.3 Manifests as prompts

Each widget ships with a JSON manifest. The manifest *is* the prompt context for the LLM router and writers, instructing them on the required props.

### 5.4 SSG rendering (no client JS)

At create/publish time, the server compiles widgets and templates into a static HTML file and uploads it. The viewer gets a static page requiring zero JavaScript.

---

## 6. Input Pipeline

Supports **Text paste** (markdown, CSV, JSON), **URL fetch**, and **PDF / image OCR extraction**. All incoming text is normalized to UTF-8 and stripped of binary noise before parsing.

---

## 7. Model Gateway

* **Cascade routing:** Uses cheap models (DeepSeek) for extraction and router tasks, routing to mid-tier models (Sonnet) for quality editing.
* **BYOK:** Users register their own keys to bypass platform rate limits.
* **Fallback chain:** Automated failover from primary provider to secondary fallback (e.g., Anthropic to OpenAI).

---

## 8. Caching

* **LLM Cache:** Hashes normalized inputs with SHA-256. Identical inputs skip the pipeline and load the existing workspace item.
* **Widget cache:** Templates are pre-cached in memory to avoid disk reads during SSG compilation.

---

## 9. Guardrail Gate

* **PII Redaction:** Scans for names, emails, and credit cards, replacing them with placeholders before passing them to LLM nodes.
* **Injection screening:** Inspects inputs for system override attempts (e.g., "ignore previous instructions") and rejects the job.

---

## 10. Evaluation & Prompt Versioning

* **Golden Set:** A suite of 100-200 input-output pairs used in CI to prevent regression during prompt or pipeline updates.
* **Prompt Versioning:** Prompts are tracked in Git. Deploying a new prompt follows a shadow → canary → A/B rollout pipeline.
* **Quality Audit:** Sampling 1-5% of traffic to score accuracy asynchronously.

---

## 11. Monitoring (pipeline-specific)

* **Distributed Tracing:** OpenTelemetry (OTel) maps spans across every pipeline node (extractor, router, writers, editor, upload) logging token counts and compute durations.
* **Alerting:** SLO-based alerting on error rates and p95 latencies.

---

## 12. Failure Handling

* **Degradation Ladder:** If the editor node fails, return the unoptimized grid layout. If all LLMs fail, load cached inputs or return a debugging error screen.
* **Circuit Breakers:** Block calls to LLM API endpoints after consecutive timeouts.

---

## 13. Data: `pipeline_runs`

Schema already exists in `005_pipeline_runs.sql`. Reserved until this RFC is activated. See [db.md](../db.md).

`workspace_items.mode = 'pipeline'` is reserved for pipeline outputs; v1 active modes are `raw` | `html` only.

---

## 14. Open Questions

1. SSE streams for real-time progress during LangGraph executions.
2. Whether a single pluggable tool should embed a mini-graph or always call this shared pipeline service.
