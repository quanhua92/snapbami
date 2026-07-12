# RFC-0005: Deferred — Chat & Telegram Bot Channel

> **Status:** Deferred  
> **Author:** Quan  
> **Created:** 2026-07-11 (content from former RFC-0002)  
> **Last Updated:** 2026-07-12  
> **Depends on:** RFC-0001 (workspaces, storage), RFC-0002 (tokens optional for agents)  
> **Former title:** RFC-0002 Chat — The Primary Interface & Telegram Bot Channel

---

## Deferral notice

**Chat is not the primary interface for v1.** Primary surfaces:

1. Minimal web workspace UI  
2. REST API  
3. MCP + API tokens ([RFC-0002](./0002-mcp-and-tokens.md))

Do not implement the chat gateway or Telegram bot until the auth + workspace + publish loop is stable and in daily use.

This document preserves the full prior design.

---

## 1. Thesis (deferred)

The chat is not "chat to a page." It's a **general-purpose AI assistant** that happens to be able to create, edit, list, and manage BamiTools pages and workspace items — similar to Claude with Artifacts or ChatGPT with Canvas.

Users could say anything:

> "Create a dashboard from this CSV" → page published in workspace  
> "Make a bar chart comparing Postgres, MySQL, MongoDB latency" → page published  
> "Change my last chart to blue" → page updated  
> "What pages have I made?" → lists workspace items  
> "Summarize this article" → text response (no page)

Pages are **artifacts** the chat produces when the user wants visual output. The chat handles everything else as normal conversation.

Channels (deferred):

1. **Web SPA Chat:** An interactive streaming UI.  
2. **Telegram Bot Chat Channel:** Webhook-driven chat with file pasting, notifications, and account linking.

---

## 2. Architecture

```
  ┌──────────────────┐         ┌──────────────────┐
  │   Web SPA Chat   │         │   Telegram Bot   │
  └────────┬─────────┘         └────────┬─────────┘
           │                            │
           │ (POST /messages)           │ (POST /webhooks/telegram)
           ▼                            ▼
┌──────────────────────────────────────────────────┐
│                   Chat Gateway                   │
│   Auth & Session checks -> Resolves User/Worksp. │
└────────────────────────┬─────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────┐
│                 LLM with Tools                   │
│   OpenAI-compatible, function calling            │
│   Tools: create_item, edit_item, list_items      │
└────────────────────────┬─────────────────────────┘
                         │ tool calls
                         ▼
┌──────────────────────────────────────────────────┐
│                 Tool Executor                    │
│   Executes S3 / tool / publish on workspaces     │
└────────────────────────┬─────────────────────────┘
                         │ results
                         ▼
┌──────────────────────────────────────────────────┐
│                 Stream Response                  │
│   Web: SSE tokens + tool previews                │
│   Telegram: Pushed message + page links          │
└──────────────────────────────────────────────────┘
```

---

## 3. Data Model

Tables already exist in `003_chat.sql`. **Reserved / deferred** until this RFC is activated. See [db.md](../db.md).

### 3.1 Conversations

```sql
CREATE TABLE conversations (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    ip_hash         TEXT,                         -- anonymous tracking
    reclaim_key     TEXT,                         -- anonymous ownership proof
    title           TEXT,                         -- auto-generated from first user message
    model           TEXT,                         -- default model for this conversation
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CHECK (
        (user_id IS NOT NULL AND ip_hash IS NULL AND reclaim_key IS NULL)
        OR
        (user_id IS NULL AND ip_hash IS NOT NULL AND reclaim_key IS NOT NULL)
    )
);
```

Conversations belong to a **user**, not a page. One user has many conversations. Each conversation has many messages. Anonymous users own conversations via a reclaim key.

### 3.2 Messages

```sql
CREATE TABLE messages (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,                -- 'user' | 'assistant' | 'tool'
    content         TEXT,                         -- message text (nullable for pure tool-call)
    tool_calls      JSONB,                        -- [{name, args}] assistant function calls
    tool_results    JSONB,                        -- [{name, result}] tool execution results
    item_id         UUID REFERENCES workspace_items(id) ON DELETE SET NULL,
    model           TEXT,
    tokens_in       INTEGER DEFAULT 0,
    tokens_out      INTEGER DEFAULT 0,
    cost_usd        NUMERIC(10,6) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Tools (chat agent)

The chat assistant is equipped with tools to read, write, and list items in the user's workspace (same capabilities as MCP):

* `list_workspace_items(directory: optional str)`
* `read_workspace_file(path: str)`
* `write_workspace_file(path: str, content: str)`
* `publish_workspace_item(path: str)`
* `delete_workspace_item(path: str)`

Later: invoke pluggable tools from [RFC-0003](./0003-pluggable-tools.md).

---

## 5. Telegram Bot Channel Integration

The Telegram Bot acts as an asynchronous, messaging-based interface to the core chat agent.

### 5.1 Account Linking Flow

1. **Initiate:** The user visits their Web UI settings and clicks "Link Telegram".
2. **Code Generation:** The server generates a single-use token: `rk_link_xxxxxx` linked to the user's `users.id` in Redis.
3. **Activation:** The user opens the Telegram bot using a deep link: `https://t.me/BamiToolsBot?start=rk_link_xxxxxx`.
4. **Binding:** The Telegram webhook parses the code, resolves the `user_id` from Redis, and updates the `users` table:

   ```sql
   UPDATE users SET telegram_chat_id = <telegram_chat_id> WHERE id = <user_id>;
   ```

### 5.2 Webhook Handling (`POST /api/webhooks/telegram`)

* **Payload Reception:** Incoming messages via FastAPI webhook.
* **Context Resolution:**
  1. Lookup `user_id` where `telegram_chat_id = <incoming_chat_id>`.
  2. If found, load the latest conversation (or create one).
  3. If not found, reply with account-linking instructions.
* **Agent Invoke:** Forward text (or file attachment) to the chat engine.
* **Response:** Format Markdown for Telegram and `sendMessage`.

### 5.3 Pastebin / File Upload via Telegram

If the user uploads a `.md`, `.csv`, `.json` file, or sends a long snippet:

1. Save to private S3: `bamitools-private/{workspace_id}/{filename}`.
2. Register in `workspace_items`.
3. Ask whether to publish or run a tool.
4. On confirm, publish and reply with `/p/{public_id}`.

### 5.4 Push Notifications

Telegram as notification stream when:

* An external agent updates a workspace file via MCP.
* A background tool or (deferred) pipeline run finishes.

---

## 6. Request Lifecycle

* **Web UI:** Message → FastAPI streaming → SSE tokens, tool previews, links.
* **Telegram:** Webhook → agent → bot push.

---

## 7. Context Window Management

* **Truncation:** Last 20 messages.
* **System Prompt:** Grounded in workspaces; prefer visual HTML artifacts when the user wants structured presentation.

---

## 8. Open Questions

1. **Telegram multi-file upload:** Batch uploads in one message.
2. **Notification limits:** Avoid spamming during long MCP edit loops.
3. **Session duration:** TTL on signed Telegram auth cookies for web-views.
