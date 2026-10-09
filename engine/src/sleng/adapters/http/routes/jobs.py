"""
Purpose:  Background video renders: POST /jobs/video, GET /jobs/{id}, GET /jobs/{id}/result.
Layer:    sleng.adapters.http.routes
Exports:  router
Depends:  sleng.adapters.http.{deps, schemas, files}, sleng.services.jobs
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import FileResponse

from sleng.adapters.http.deps import EngineDep
from sleng.adapters.http.files import SEED_HEADER, doc
from sleng.adapters.http.schemas.requests import VideoJobIn
from sleng.adapters.http.schemas.responses import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])
MP4_DOC = doc("video/mp4", "The rendered video")


@router.post("/video", status_code=202)
def start_video(body: VideoJobIn, engine: EngineDep) -> JobOut:
    """Start rendering an MP4. Poll GET /jobs/{id} until done, then GET /jobs/{id}/result."""
    request = body.to_video_request()

    def task(path: Path, report: Callable[[float], None]) -> dict[str, Any]:
        return {"seed": engine.video.render(request, path, report)}

    return JobOut.from_view(engine.jobs.submit("video", "video/mp4", ".mp4", task))


@router.get("/{job_id}")
def job_status(job_id: str, engine: EngineDep) -> JobOut:
    """Status and progress (0..1) of a job; `meta.seed` holds a video's design number."""
    return JobOut.from_view(engine.jobs.get(job_id))


@router.get("/{job_id}/result", response_class=FileResponse, responses=MP4_DOC)
def job_result(job_id: str, engine: EngineDep) -> FileResponse:
    """The finished file (409 while the job is still running)."""
    path, media_type = engine.jobs.result(job_id)
    seed = engine.jobs.get(job_id).meta.get("seed")
    headers = {SEED_HEADER: str(seed)} if seed is not None else None
    filename = f"sleng-{job_id[:8]}{path.suffix}"
    return FileResponse(path, media_type=media_type, filename=filename, headers=headers)
