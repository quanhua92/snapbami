CREATE TABLE IF NOT EXISTS dashboards (
    id              UUID DEFAULT uuidv7() PRIMARY KEY,
    public_id       VARCHAR(8) UNIQUE NOT NULL,
    owner_uid       TEXT NOT NULL,
    owner_username  VARCHAR(20),
    content_hash    CHAR(64),
    mode            VARCHAR(20) NOT NULL,
    reclaim_key     VARCHAR(40),
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    firebase_uid    TEXT PRIMARY KEY,
    username        VARCHAR(20) UNIQUE,
    display_name    VARCHAR(100),
    email           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
