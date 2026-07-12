-- Credentials: user BYOK keys, user access tokens, platform system credentials

CREATE TABLE IF NOT EXISTS byok_keys (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label           TEXT,                        -- user-facing name, e.g. "My OpenAI key"
    provider        TEXT NOT NULL,               -- 'openai' | 'deepseek' | 'anthropic' | 'ollama'
    base_url        TEXT NOT NULL,
    api_key         TEXT NOT NULL,               -- encrypted at rest
    model           TEXT,                        -- preferred model
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS access_tokens (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label           TEXT,                        -- user-facing name, e.g. "Cursor MCP"
    key_hash        TEXT NOT NULL UNIQUE,        -- SHA-256 hash of the token
    key_prefix      TEXT NOT NULL,               -- e.g. "btk_abc1..."
    is_active       BOOLEAN DEFAULT TRUE,
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_credentials (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    service         TEXT NOT NULL,               -- 'openai' | 'deepseek' | 's3' | etc.
    base_url        TEXT,
    api_key         TEXT NOT NULL,               -- encrypted at rest
    model           TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_byok_keys_user_id
    ON byok_keys(user_id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_access_tokens_user_id
    ON access_tokens(user_id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_access_tokens_key_hash
    ON access_tokens(key_hash) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_system_credentials_service
    ON system_credentials(service) WHERE is_active = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_system_credentials_service_active
    ON system_credentials(service) WHERE is_active = TRUE;
