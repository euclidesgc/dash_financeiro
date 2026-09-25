from pathlib import Path

from fastapi import FastAPI
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.staticfiles import StaticFiles

SPA_MISSING = "SPA não compilada: rode pnpm build"


def mount_spa(app: FastAPI, dist: Path) -> None:
    # Reason: StaticFiles refuses a nonexistent directory at construction
    # time, and the Python CI runs without pnpm build.
    if (dist / "assets").is_dir():
        app.mount("/app/assets", StaticFiles(directory=dist / "assets"), name="spa-assets")

    @app.get("/app")
    @app.get("/app/{path:path}")
    def spa_index() -> Response:
        index = dist / "index.html"
        if index.exists():
            return FileResponse(index, media_type="text/html")
        return JSONResponse({"detail": SPA_MISSING}, status_code=503)
