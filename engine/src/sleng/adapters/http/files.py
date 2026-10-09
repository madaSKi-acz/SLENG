"""
Purpose:  Binary responses (WAV, zip, SRT downloads), upload reading, and the custom headers.
Layer:    sleng.adapters.http
Exports:  GAP_HEADER, SEED_HEADER, EXPOSED_HEADERS, WAV_DOC, doc, binary, read_upload
Depends:  fastapi, sleng.domain.errors
"""

from __future__ import annotations

from typing import Any

from fastapi import Response, UploadFile

from sleng.domain.errors import InvalidInputError

GAP_HEADER = "X-Gap-After"  # seconds of silence to leave after a line (POST /speech/line)
SEED_HEADER = "X-Seed"  # design number of a rendered video
EXPOSED_HEADERS = (GAP_HEADER, SEED_HEADER, "Content-Disposition")
MEGABYTE = 1024 * 1024
ResponseDoc = dict[int | str, dict[str, Any]]


def doc(media_type: str, description: str) -> ResponseDoc:
    """OpenAPI description of a binary 200 response."""
    return {200: {"content": {media_type: {}}, "description": description}}


WAV_DOC = doc("audio/wav", "WAV audio (16-bit PCM, mono)")


def binary(
    data: bytes,
    media_type: str,
    filename: str | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    """Raw bytes; with a filename the browser saves it as a download."""
    all_headers = dict(headers or {})
    if filename:
        all_headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return Response(content=data, media_type=media_type, headers=all_headers)


def read_upload(upload: UploadFile, max_mb: int) -> bytes:
    """The uploaded file's bytes, refusing anything over `max_mb` megabytes."""
    limit = max_mb * MEGABYTE
    data = upload.file.read(limit + 1)
    if len(data) > limit:
        raise InvalidInputError(f"The file is larger than {max_mb} MB.")
    return data
