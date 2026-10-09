"""
Purpose:  Build the FastAPI application around one Sleng engine.
Layer:    sleng.adapters.http
Exports:  create_app, API_PREFIX
Depends:  fastapi, sleng.container, sleng.adapters.http.{routes, errors, files}
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sleng import __version__
from sleng.adapters.http.errors import install_error_handlers
from sleng.adapters.http.files import EXPOSED_HEADERS
from sleng.adapters.http.routes import ROUTERS
from sleng.container import Sleng

API_PREFIX = "/api/v1"
Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(engine: Sleng | None = None) -> FastAPI:
    """The HTTP app. Pass an engine to share it (tests, embedding); otherwise one is built."""
    engine = engine or Sleng()
    app = FastAPI(
        title="SLENG engine",
        version=__version__,
        description="Khmer text-to-speech: voices, cloning, audio and video export.",
        lifespan=_lifespan(engine),
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.engine = engine
    _add_cors(app, engine.settings.cors_origins)
    install_error_handlers(app)
    for router in ROUTERS:
        app.include_router(router, prefix=API_PREFIX)
    _mount_web(app, engine.settings.resolved_web_dist())
    return app


def _lifespan(engine: Sleng) -> Lifespan:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        engine.warm_up()
        yield
        engine.close()

    return lifespan


def _add_cors(app: FastAPI, origins: tuple[str, ...]) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(origins),
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=list(EXPOSED_HEADERS),
    )


def _mount_web(app: FastAPI, dist: Path | None) -> None:
    """Serve the built UI at "/" (after the API routes, so /api/* always wins)."""
    if dist is not None:
        app.mount("/", StaticFiles(directory=dist, html=True), name="web")
