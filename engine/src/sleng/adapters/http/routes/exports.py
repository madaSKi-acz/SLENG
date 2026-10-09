"""
Purpose:  POST /exports/{wav,zip,srt}: whole-script downloads.
Layer:    sleng.adapters.http.routes
Exports:  router
Depends:  sleng.adapters.http.{deps, schemas, files}
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from sleng.adapters.http.deps import EngineDep
from sleng.adapters.http.files import WAV_DOC, binary, doc
from sleng.adapters.http.schemas.requests import NarrationIn

router = APIRouter(prefix="/exports", tags=["exports"])
ZIP_DOC = doc("application/zip", "One WAV per line")
SRT_DOC = doc("application/x-subrip", "SubRip subtitles")


@router.post("/wav", response_class=Response, responses=WAV_DOC)
def export_wav(body: NarrationIn, engine: EngineDep) -> Response:
    """The whole script as one WAV (smart merge: even loudness, natural gaps)."""
    return binary(engine.exports.wav(body.to_domain()), "audio/wav", "sleng.wav")


@router.post("/zip", response_class=Response, responses=ZIP_DOC)
def export_zip(body: NarrationIn, engine: EngineDep) -> Response:
    """001.wav, 002.wav... one per line, plus chunks.txt."""
    data = engine.exports.zip(body.script.to_domain(), body.speech.to_domain())
    return binary(data, "application/zip", "sleng-lines.zip")


@router.post("/srt", response_class=Response, responses=SRT_DOC)
def export_srt(body: NarrationIn, engine: EngineDep) -> Response:
    """Subtitles timed to the narration (CapCut, Premiere, DaVinci)."""
    text = engine.exports.srt(body.to_domain())
    return binary(text.encode("utf-8"), "application/x-subrip; charset=utf-8", "sleng.srt")
