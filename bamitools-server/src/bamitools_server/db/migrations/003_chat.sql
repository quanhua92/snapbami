-- Chat: conversations + messages + attachments

CREATE TABLE IF NOT EXISTS conversations (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    ip_hash         TEXT,                         -- anonymous tracking
    reclaim_key     TEXT,                         -- anonymous ownership proof
    title           TEXT,                         -- auto-generated
    model           TEXT,                         -- default model
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CHECK (
        (user_id IS NOT NULL AND ip_hash IS NULL AND reclaim_key IS NULL)
        OR
        (user_id IS NULL AND ip_hash IS NOT NULL AND reclaim_key IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS messages (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,                -- 'user' | 'assistant' | 'tool'
    content         TEXT,
    tool_calls      JSONB,                        -- [{name, args}]
    tool_results    JSONB,                        -- [{name, result}]
    item_id         UUID REFERENCES workspace_items(id) ON DELETE SET NULL, -- page created/modified
    model           TEXT,
    tokens_in       INTEGER DEFAULT 0,
    tokens_out      INTEGER DEFAULT 0,
    cost_usd        NUMERIC(10,6) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS attachments (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    message_id      UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    s3_key          TEXT NOT NULL,               -- 'attachments/{id}/{filename}'
    filename        TEXT,
    content_type    TEXT,
    size_bytes      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id_updated_at
    ON conversations(user_id, updated_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_ip_hash_updated_at
    ON conversations(ip_hash, updated_at DESC) WHERE ip_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_reclaim_key
    ON conversations(reclaim_key) WHERE reclaim_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id_created_at
    ON messages(conversation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_item_id
    ON messages(item_id) WHERE item_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_attachments_message_id
    ON attachments(message_id);
