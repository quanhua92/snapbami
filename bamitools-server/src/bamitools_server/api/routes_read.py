import json
import re

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from bamitools_server.cache.redis import get_redis
from bamitools_server.storage.s3 import get_public_object

router = APIRouter()

_CACHE_TTL = 30
_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{1,20}$")


@router.get("/p/{public_id}.json")
async def read_page_json(public_id: str):
    if not _ID_PATTERN.match(public_id):
        return JSONResponse(status_code=400, content={"error": "Invalid ID"})
    redis = await get_redis()
    cache_key = f"page:{public_id}.json"
    try:
        cached = await redis.get(cache_key)
        if cached:
            return JSONResponse(content=json.loads(cached))
    except Exception:
        pass

    data = await get_public_object(f"{public_id}.json")
    if data is None:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    try:
        await redis.setex(cache_key, _CACHE_TTL, data)
    except Exception:
        pass
    return JSONResponse(content=json.loads(data))


@router.get("/p/{public_id}")
async def read_page_html(public_id: str):
    if not _ID_PATTERN.match(public_id):
        return HTMLResponse(status_code=400, content="Invalid ID")
    redis = await get_redis()
    cache_key = f"page:{public_id}"
    try:
        cached = await redis.get(cache_key)
        if cached:
            return HTMLResponse(content=cached)
    except Exception:
        pass

    data = await get_public_object(public_id)
    if data is None:
        return HTMLResponse(status_code=404, content="Not found")
    html = data.decode()
    try:
        await redis.setex(cache_key, _CACHE_TTL, html)
    except Exception:
        pass
    return HTMLResponse(content=html)
