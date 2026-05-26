import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Reminder Bot API", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")

    dist = os.path.join(os.path.dirname(__file__), "..", "mini_app", "dist")
    if os.path.exists(dist):
        app.mount("/", StaticFiles(directory=dist, html=True), name="static")

    return app
