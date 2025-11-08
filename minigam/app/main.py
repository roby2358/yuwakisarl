from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "resources" / "public"


def create_app() -> FastAPI:
    app = FastAPI(title="MINIGAM")
    app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> FileResponse:
        return FileResponse(PUBLIC_DIR / "index.html")

    return app


app = create_app()

