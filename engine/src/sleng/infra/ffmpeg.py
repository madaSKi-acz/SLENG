"""
Purpose:  Find the ffmpeg binary once and run it, either as a pipe or as a long-running encode.
Layer:    sleng.infra
Exports:  Ffmpeg, FfmpegError
Depends:  imageio_ffmpeg (bundled binary, preferred) or `ffmpeg` on PATH; sleng.domain.errors
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import IO

from sleng.domain.errors import DependencyError, SlengError

BASE_ARGS = ("-hide_banner", "-loglevel", "error")


class FfmpegError(SlengError):
    """ffmpeg exited with an error; the message ends with the tail of its stderr."""


class Ffmpeg:
    """The ffmpeg executable, located lazily on first use."""

    def __init__(self, executable: str | None = None) -> None:
        self._executable = executable

    @property
    def executable(self) -> str:
        if self._executable is None:
            self._executable = _locate()
        return self._executable

    def pipe(self, args: list[str], data: bytes | None = None) -> bytes:
        """Run once with `data` on stdin and return stdout. Raises FfmpegError on failure."""
        proc = subprocess.run(
            [self.executable, *BASE_ARGS, *args], input=data, capture_output=True, check=False
        )
        if proc.returncode or not proc.stdout:
            raise FfmpegError(_tail(proc.stderr))
        return proc.stdout

    def spawn(
        self, args: list[str], cwd: Path, stdin: int, log: IO[str]
    ) -> subprocess.Popen[bytes]:
        """Start a long run (a video encode); the caller feeds stdin, stderr goes to `log`."""
        command = [self.executable, *BASE_ARGS, *args]
        return subprocess.Popen(command, cwd=cwd, stdin=stdin, stderr=log)


def _tail(stderr: bytes, size: int = 300) -> str:
    return stderr.decode(errors="replace").strip()[-size:]


def _locate() -> str:
    found = _bundled() or shutil.which("ffmpeg")
    if not found:
        raise DependencyError(
            f"ffmpeg not found. Install it with: {sys.executable} -m pip install imageio-ffmpeg"
        )
    return found


def _bundled() -> str | None:
    try:
        import imageio_ffmpeg

        return str(imageio_ffmpeg.get_ffmpeg_exe())
    # Any failure here just means "no bundled binary".
    except Exception:  # noqa: BLE001
        return None
