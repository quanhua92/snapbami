CREATE INDEX IF NOT EXISTS idx_dashboards_content_hash
    ON dashboards(content_hash) WHERE content_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_dashboards_reclaim_key
    ON dashboards(reclaim_key) WHERE reclaim_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_dashboards_owner_uid
    ON dashboards(owner_uid);

CREATE INDEX IF NOT EXISTS idx_dashboards_expires_at
    ON dashboards(expires_at) WHERE expires_at IS NOT NULL;
