from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bamitools_server.api.routes_read import router as read_router
from bamitools_server.api.routes_spa import router as spa_router
from bamitools_server.cache.redis import get_redis
from bamitools_server.db.pool import close_pool, init_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await get_redis()
    yield
    await close_pool()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Order matters: specific routes before SPA catch-all
app.include_router(read_router)
app.include_router(spa_router)
