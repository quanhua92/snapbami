import pathlib

MIGRATION_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "src"
    / "snapbami_server"
    / "db"
    / "migrations"
)


def test_migration_files_exist():
    sql_files = sorted(MIGRATION_DIR.glob("*.sql"))
    assert len(sql_files) >= 2


def test_001_creates_dashboards_table():
    sql = (MIGRATION_DIR / "001_dashboards.sql").read_text()
    assert "CREATE TABLE" in sql
    assert "dashboards" in sql
    assert "users" in sql


def test_001_has_uuid_v7():
    sql = (MIGRATION_DIR / "001_dashboards.sql").read_text()
    assert "uuidv7()" in sql


def test_001_dashboards_columns():
    sql = (MIGRATION_DIR / "001_dashboards.sql").read_text().lower()
    for col in [
        "public_id",
        "owner_uid",
        "content_hash",
        "mode",
        "reclaim_key",
        "expires_at",
        "created_at",
    ]:
        assert col in sql, f"Missing column: {col}"


def test_001_users_columns():
    sql = (MIGRATION_DIR / "001_dashboards.sql").read_text().lower()
    for col in ["firebase_uid", "username", "display_name", "email"]:
        assert col in sql, f"Missing column: {col}"


def test_002_creates_indexes():
    sql = (MIGRATION_DIR / "002_indexes.sql").read_text()
    assert "CREATE INDEX" in sql
    for idx in ["content_hash", "reclaim_key", "owner_uid", "expires_at"]:
        assert idx in sql, f"Missing index on: {idx}"
