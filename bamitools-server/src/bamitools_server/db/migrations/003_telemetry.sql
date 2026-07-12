-- Usage logging + content reports

CREATE TABLE IF NOT EXISTS usage_log (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    ip_hash         TEXT,
    action          TEXT NOT NULL,               -- 'publish' | 'update' | 'deploy' | 'view' | 'chat'
    item_id         UUID REFERENCES workspace_items(id) ON DELETE SET NULL,
    source_type     TEXT,                        -- 'text' | 'url' | 'pdf' | 'raw'
    model           TEXT,
    tokens_in       INTEGER DEFAULT 0,
    tokens_out      INTEGER DEFAULT 0,
    cost_usd        NUMERIC(10,6) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    item_id         UUID REFERENCES workspace_items(id) ON DELETE CASCADE,
    reporter_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    reason          TEXT,                       -- 'phishing' | 'malware' | 'spam'
    status          TEXT DEFAULT 'pending',     -- 'pending' | 'actioned' | 'dismissed'
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_log_user_id_created_at
    ON usage_log(user_id, created_at DESC) WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_usage_log_ip_hash_created_at
    ON usage_log(ip_hash, created_at DESC) WHERE ip_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_usage_log_action_created_at
    ON usage_log(action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reports_item_id
    ON reports(item_id) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_reports_status
    ON reports(status) WHERE status = 'pending';
