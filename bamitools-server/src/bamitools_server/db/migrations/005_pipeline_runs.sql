-- Pipeline execution tracking

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    item_id         UUID REFERENCES workspace_items(id) ON DELETE CASCADE,
    wall_time_ms    INTEGER,
    llm_calls       SMALLINT,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    cost_usd        NUMERIC(10,6),
    model_extract   TEXT,
    model_edit      TEXT,
    prompt_versions JSONB DEFAULT '{}',
    cached          BOOLEAN DEFAULT FALSE,
    status          TEXT DEFAULT 'ok',          -- 'ok' | 'partial' | 'failed'
    trace_id        TEXT,
    error           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_item_id
    ON pipeline_runs(item_id);
