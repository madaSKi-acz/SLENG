"""
Purpose:  POST /text/split (lines as the engine reads them) and POST /speech/line (one line, WAV).
Layer:    sleng.adapters.http.routes
Exports:  router
Depends:  sleng.adapters.http.{deps, schemas, files}, sleng.audio.wav
Notes:    Sync handlers on purpose: they run in FastAPI's thread pool, which the voice engines need.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from sleng.adapters.http.deps import EngineDep
from sleng.adapters.http.files import GAP_HEADER, WAV_DOC, binary
from sleng.adapters.http.schemas.requests import LineSpeechIn, SplitIn
from sleng.adapters.http.schemas.responses import ChunkOut
from sleng.audio.wav import encode_wav

router = APIRouter(tags=["speech"])


@router.post("/text/split")
def split_text(body: SplitIn, engine: EngineDep) -> list[ChunkOut]:
    """Split text into lines (sentences, long ones cut at spaces) with the pause after each."""
    chunks = engine.speech.split(body.text, body.max_chars)
    return [ChunkOut.from_domain(chunk) for chunk in chunks]


@router.post("/speech/line", response_class=Response, responses=WAV_DOC)
def speak_line(body: LineSpeechIn, engine: EngineDep) -> Response:
    """One line as WAV. The X-Gap-After header gives the seconds to wait before the next line."""
    audio = engine.speech.speak_line(body.text, body.speech.to_domain())
    gap = body.pauses.to_domain().gap_after(body.pause)
    return binary(encode_wav(audio), "audio/wav", headers={GAP_HEADER: f"{gap:.3f}"})
