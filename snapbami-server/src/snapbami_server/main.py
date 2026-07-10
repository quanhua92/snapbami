import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from snapbami_server.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: pool, redis, firebase wired in later phases
    yield
    # Shutdown


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve static assets (js, css, images) and SPA fallback for client-side routing.
_STATIC_DIR = settings.STATIC_DIR
_index_html = os.path.join(_STATIC_DIR, "index.html")

if os.path.isdir(_STATIC_DIR):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")),
        name="assets",
    )

    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        file_path = os.path.join(_STATIC_DIR, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(_index_html)
