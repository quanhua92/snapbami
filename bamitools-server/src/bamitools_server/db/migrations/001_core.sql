-- Core entities: users, workspaces, and workspace_items

CREATE TABLE IF NOT EXISTS users (
    id               UUID DEFAULT uuidv7() PRIMARY KEY,
    auth_provider    TEXT DEFAULT 'firebase',           -- 'firebase' | 'clerk' | 'local'
    auth_uid         TEXT UNIQUE NOT NULL,              -- Provider UID (Firebase UID)
    username         TEXT UNIQUE,                       -- Unique user handle
    display_name     TEXT,
    email            TEXT UNIQUE,
    tier             TEXT DEFAULT 'free',               -- 'free' | 'pro' | 'max'
    telegram_chat_id BIGINT UNIQUE,                     -- Account linkage
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    owner_id        UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL allowed for anonymous guest workspace
    name            TEXT NOT NULL,                      -- e.g. "Personal Workspace"
    slug            TEXT NOT NULL,                      -- e.g. "personal"
    meta            JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspace_items (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    path            TEXT NOT NULL,                      -- e.g. 'notes/todo.md'
    public_id       TEXT UNIQUE,                        -- e.g. 'tY7b8cDe' (NULL if private)
    title           TEXT,
    content_hash    TEXT,
    size_bytes      INTEGER NOT NULL DEFAULT 0,         -- object byte size, for quota accounting (D8)
    mode            TEXT NOT NULL,                      -- 'html' | 'pipeline' | 'raw'
    reclaim_key     TEXT,                               -- Recovery token for guest items
    password_hash   TEXT,                               -- Password hash for secure share links (/s/)
    meta            JSONB DEFAULT '{}',                 -- content-type, original size, etc.
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (workspace_id, path)
);

-- Seed the permanent Global Guest Workspace
INSERT INTO workspaces (id, owner_id, name, slug)
VALUES ('00000000-0000-0000-0000-000000000000', NULL, 'Global Guest Workspace', 'guest')
ON CONFLICT (id) DO NOTHING;

-- ==================== INDEXES ====================

-- Ensure registered users have unique workspace slugs
CREATE UNIQUE INDEX IF NOT EXISTS uq_workspaces_owner_slug
    ON workspaces(owner_id, slug) WHERE owner_id IS NOT NULL;

-- Ensure anonymous guest workspace slugs are globally unique
CREATE UNIQUE INDEX IF NOT EXISTS uq_workspaces_anon_slug
    ON workspaces(slug) WHERE owner_id IS NULL;

-- Index for resolving published pages
CREATE INDEX IF NOT EXISTS idx_workspace_items_public_id
    ON workspace_items(public_id) WHERE public_id IS NOT NULL;

-- Index for caching checks
CREATE INDEX IF NOT EXISTS idx_workspace_items_content_hash
    ON workspace_items(content_hash) WHERE content_hash IS NOT NULL;

-- Unique lookup for guest claim (D9): reclaim_key is the claim capability
CREATE UNIQUE INDEX IF NOT EXISTS uq_workspace_items_reclaim_key
    ON workspace_items(reclaim_key) WHERE reclaim_key IS NOT NULL;

-- Index for TTL cleanup
CREATE INDEX IF NOT EXISTS idx_workspace_items_expires_at
    ON workspace_items(expires_at) WHERE expires_at IS NOT NULL;
