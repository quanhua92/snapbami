import asyncio
import pathlib

import asyncpg

from snapbami_server.config import settings

MIGRATION_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "src"
    / "snapbami_server"
    / "db"
    / "migrations"
)

CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS _migrations (
    name        TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ DEFAULT NOW()
)
"""


async def run_migrations() -> None:
    conn = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        await conn.execute(CREATE_MIGRATIONS_TABLE)

        applied = {
            row["name"] for row in await conn.fetch("SELECT name FROM _migrations")
        }

        sql_files = sorted(MIGRATION_DIR.glob("*.sql"))
        if not sql_files:
            print("No migration files found.")
            return

        for sql_file in sql_files:
            name = sql_file.name
            if name in applied:
                print(f"  skipped: {name} (already applied)")
                continue
            sql = sql_file.read_text()
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute("INSERT INTO _migrations (name) VALUES ($1)", name)
            print(f"  applied: {name}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
