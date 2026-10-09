"""
Purpose:  Background jobs for long work (video renders): submit, poll progress, fetch the result.
Layer:    sleng.services
Exports:  JobManager, JobView, JobStatus, JobTask
Depends:  standard library, sleng.domain.errors
Notes:    In-process thread pool, results kept on disk. To scale out, keep this interface and back
          it with a real queue (RQ, Celery, a cloud task queue) plus shared storage.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from sleng.domain.errors import ConflictError, NotFoundError, SlengError

log = logging.getLogger(__name__)
STALE_SECONDS = 24 * 3600  # results older than this, left by earlier runs, are deleted
JobTask = Callable[[Path, Callable[[float], None]], dict[str, Any]]


class JobStatus(str, Enum):
    """Lifecycle of a job."""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass(frozen=True)
class JobView:
    """Read-only snapshot of a job for callers."""

    id: str
    kind: str
    status: JobStatus
    progress: float
    error: str | None
    meta: dict[str, Any]
    created: float


@dataclass
class _Job:
    id: str
    kind: str
    path: Path
    media_type: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    created: float = field(default_factory=time.time)

    def report(self, done: float) -> None:
        self.progress = min(max(done, 0.0), 1.0)

    def view(self) -> JobView:
        return JobView(
            id=self.id,
            kind=self.kind,
            status=self.status,
            progress=self.progress,
            error=self.error,
            meta=dict(self.meta),
            created=self.created,
        )


class JobManager:
    """Runs tasks on a small thread pool and keeps the last `keep` finished results."""

    def __init__(self, workdir: Path, workers: int = 1, keep: int = 20) -> None:
        _sweep(workdir, STALE_SECONDS)
        self._dir = workdir
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="sleng-job")
        self._jobs: OrderedDict[str, _Job] = OrderedDict()
        self._lock = threading.Lock()
        self._keep = keep

    def submit(self, kind: str, media_type: str, suffix: str, task: JobTask) -> JobView:
        """Queue `task(output_path, report_progress) -> meta` and return its first snapshot."""
        self._dir.mkdir(parents=True, exist_ok=True)
        job_id = uuid.uuid4().hex
        job = _Job(job_id, kind, self._dir / f"{job_id}{suffix}", media_type)
        with self._lock:
            self._jobs[job_id] = job
            self._prune()
        self._pool.submit(self._run, job, task)
        return job.view()

    def get(self, job_id: str) -> JobView:
        return self._find(job_id).view()

    def result(self, job_id: str) -> tuple[Path, str]:
        """(file path, media type) of a finished job."""
        job = self._find(job_id)
        if job.status is not JobStatus.DONE:
            raise ConflictError(f"Job {job_id} is {job.status.value}, not done.")
        return job.path, job.media_type

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _run(self, job: _Job, task: JobTask) -> None:
        job.status = JobStatus.RUNNING
        try:
            job.meta = task(job.path, job.report)
            job.progress, job.status = 1.0, JobStatus.DONE
        # Reported through the job, never lost in a thread.
        except Exception as err:
            log.exception("Job %s (%s) failed", job.id, job.kind)
            job.error = str(err) if isinstance(err, SlengError) else "Internal error. See the log."
            job.status = JobStatus.FAILED

    def _find(self, job_id: str) -> _Job:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise NotFoundError(f"Unknown job: {job_id}")
        return job

    def _prune(self) -> None:
        finished = [job for job in self._jobs.values() if job.status in _FINISHED]
        for job in finished[: max(0, len(self._jobs) - self._keep)]:
            del self._jobs[job.id]
            job.path.unlink(missing_ok=True)


_FINISHED = (JobStatus.DONE, JobStatus.FAILED)


def _sweep(workdir: Path, max_age: float) -> None:
    """Delete old result files (another process may share the folder, so never all of them)."""
    if not workdir.is_dir():
        return
    cutoff = time.time() - max_age
    for path in workdir.iterdir():
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)
