import asyncpg

from bamitools_server.config import settings

pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    global pool
    pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=2,
        max_size=10,
    )
    return pool


async def get_pool() -> asyncpg.Pool:
    if pool is None:
        await init_pool()
    assert pool is not None
    return pool


async def close_pool() -> None:
    global pool
    if pool is not None:
        await pool.close()
        pool = None
