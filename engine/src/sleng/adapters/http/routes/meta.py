"""
Purpose:  GET /health (liveness, version) and GET /options (themes, palettes, sizes, cleanup).
Layer:    sleng.adapters.http.routes
Exports:  router
Depends:  sleng.adapters.http.{deps, schemas}, sleng.media.palettes, sleng.domain
"""

from __future__ import annotations

from fastapi import APIRouter

from sleng import __version__
from sleng.adapters.http.deps import EngineDep
from sleng.adapters.http.schemas.responses import HealthOut, OptionsOut, PaletteOut, SizeOut
from sleng.domain import VIDEO_SIZES, CleanupLevel, VideoTheme
from sleng.media.palettes import palette_groups

router = APIRouter(tags=["meta"])


@router.get("/health")
def health(engine: EngineDep) -> HealthOut:
    """The engine is up; `fake` means test voices (no models, no network)."""
    return HealthOut(status="ok", version=__version__, fake=engine.settings.fake)


@router.get("/options")
def options() -> OptionsOut:
    """Everything the UI offers in its pickers comes from here."""
    return OptionsOut(
        themes=list(VideoTheme),
        palettes=[PaletteOut(name=name, group=group) for name, group in palette_groups()],
        sizes=[SizeOut(width=width, height=height) for width, height in VIDEO_SIZES],
        cleanup_levels=list(CleanupLevel),
    )
