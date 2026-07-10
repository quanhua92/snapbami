import redis.asyncio as redis

from snapbami_server.config import settings

redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client
