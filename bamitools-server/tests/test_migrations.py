import pathlib

MIGRATION_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "src"
    / "bamitools_server"
    / "db"
    / "migrations"
)


def test_migration_files_exist():
    sql_files = sorted(MIGRATION_DIR.glob("*.sql"))
    assert len(sql_files) >= 5


def test_001_creates_core_tables():
    sql = (MIGRATION_DIR / "001_core.sql").read_text()
    assert "CREATE TABLE" in sql
    assert "users" in sql
    assert "workspaces" in sql
    assert "workspace_items" in sql


def test_001_has_uuid_v7():
    sql = (MIGRATION_DIR / "001_core.sql").read_text()
    assert "uuidv7()" in sql


def test_001_users_columns():
    sql = (MIGRATION_DIR / "001_core.sql").read_text().lower()
    for col in ["auth_provider", "auth_uid", "username", "display_name", "email"]:
        assert col in sql, f"Missing users column: {col}"


def test_001_workspaces_columns():
    sql = (MIGRATION_DIR / "001_core.sql").read_text().lower()
    for col in ["owner_id", "name", "slug"]:
        assert col in sql, f"Missing workspaces column: {col}"


def test_001_workspace_items_columns():
    sql = (MIGRATION_DIR / "001_core.sql").read_text().lower()
    for col in [
        "workspace_id",
        "path",
        "public_id",
        "mode",
        "reclaim_key",
        "password_hash",
        "expires_at",
    ]:
        assert col in sql, f"Missing workspace_items column: {col}"


def test_001_guest_workspace_seeded():
    sql = (MIGRATION_DIR / "001_core.sql").read_text()
    assert "00000000-0000-0000-0000-000000000000" in sql
    assert "Global Guest Workspace" in sql


def test_002_credentials_tables():
    sql = (MIGRATION_DIR / "002_credentials.sql").read_text()
    assert "byok_keys" in sql
    assert "access_tokens" in sql
    assert "system_credentials" in sql
