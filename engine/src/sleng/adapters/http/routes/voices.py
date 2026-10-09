"""
Purpose:  Voices: GET /voices, POST /voices (clone from a clip), POST /voices/preview, DELETE.
Layer:    sleng.adapters.http.routes
Exports:  router
Depends:  sleng.adapters.http.{deps, schemas, files}, sleng.services.voices
Notes:    Clips arrive as multipart uploads (no base64), capped at settings.max_upload_mb.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, Response, UploadFile

from sleng.adapters.http.deps import EngineDep
from sleng.adapters.http.files import WAV_DOC, binary, read_upload
from sleng.adapters.http.schemas.responses import VoiceOut
from sleng.domain import Gender
from sleng.services.voices import CloneRequest

router = APIRouter(prefix="/voices", tags=["voices"])


@router.get("")
def list_voices(engine: EngineDep) -> list[VoiceOut]:
    """Built-in voices first, then cloned voices (oldest first)."""
    return [VoiceOut.from_domain(info) for info in engine.voices.voices()]


# FastAPI declares multipart form fields as parameters, so this signature is wider than usual.
@router.post("", status_code=201)
def clone_voice(  # noqa: PLR0913
    engine: EngineDep,
    clip: UploadFile,
    name: Annotated[str, Form(max_length=80)],
    gender: Annotated[Gender, Form()],
    base_id: Annotated[str | None, Form()] = None,
    clean: Annotated[bool, Form()] = True,
) -> VoiceOut:
    """Save a voice cloned from 10-30 s of one person speaking (first use downloads ~130 MB)."""
    audio = read_upload(clip, engine.settings.max_upload_mb)
    request = CloneRequest(name, gender, audio, base_id or None, clean)
    return VoiceOut.from_domain(engine.voices.clone(request))


@router.post("/preview", response_class=Response, responses=WAV_DOC)
def preview_clip(
    engine: EngineDep, clip: UploadFile, clean: Annotated[bool, Form()] = True
) -> Response:
    """The clip exactly as it would be cloned (cleaned or original), to listen before saving."""
    audio = read_upload(clip, engine.settings.max_upload_mb)
    return binary(engine.voices.preview(audio, clean), "audio/wav")


@router.delete("/{voice_id}", status_code=204, response_class=Response)
def delete_voice(voice_id: str, engine: EngineDep) -> Response:
    """Delete a cloned voice and its recording from this computer."""
    engine.voices.delete(voice_id)
    return Response(status_code=204)
