import os

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from bamitools_server.config import settings

router = APIRouter()

_STATIC_DIR = os.path.realpath(settings.STATIC_DIR)
_index_html = os.path.join(_STATIC_DIR, "index.html")

if os.path.isdir(_STATIC_DIR):
    router.mount(
        "/assets",
        StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")),
        name="assets",
    )

    @router.get("/{path:path}")
    async def spa_fallback(path: str):
        file_path = os.path.realpath(os.path.join(_STATIC_DIR, path))
        if (
            path
            and os.path.isfile(file_path)
            and file_path.startswith(_STATIC_DIR + os.sep)
        ):
            return FileResponse(file_path)
        return FileResponse(_index_html)
