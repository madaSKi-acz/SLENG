"""
Purpose:  Engine settings: defaults < SLENG_* environment variables < explicit overrides.
Layer:    sleng.config
Exports:  Settings, DEFAULT_CORS_ORIGINS
Depends:  standard library only
Notes:    data_dir defaults to the working directory, so `sleng serve` run from the repo root keeps
          using ./voices (existing clones) and serves ./web/dist when it has been built.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "tauri://localhost",  # desktop shell (Tauri) on macOS/Linux
    "http://tauri.localhost",  # desktop shell (Tauri) on Windows
    "https://tauri.localhost",
)


def _flag(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _origins(value: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())


_ENV: dict[str, tuple[str, Callable[[str], Any]]] = {
    "data_dir": ("SLENG_DATA_DIR", Path),
    "device": ("SLENG_DEVICE", str),
    "fake": ("SLENG_FAKE", _flag),
    "font_path": ("SLENG_FONT", Path),
    "font_family": ("SLENG_FONT_FAMILY", str),
    "web_dist": ("SLENG_WEB_DIST", Path),
    "cors_origins": ("SLENG_CORS_ORIGINS", _origins),
    "max_upload_mb": ("SLENG_MAX_UPLOAD_MB", int),
    "job_workers": ("SLENG_JOB_WORKERS", int),
}


@dataclass(frozen=True)
class Settings:
    """Everything configurable about one engine process."""

    data_dir: Path = field(default_factory=Path.cwd)
    device: str | None = None  # "cpu" / "cuda"; None = auto
    fake: bool = False  # tones instead of models: tests and UI work, no network
    font_path: Path | None = None  # custom subtitle font instead of Kantumruy Pro
    font_family: str | None = None
    web_dist: Path | None = None  # built web UI to serve at "/"
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    max_upload_mb: int = 25
    job_workers: int = 1  # parallel video renders

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None, **overrides: Any) -> Settings:
        """Read SLENG_* variables, then apply every override that is not None."""
        env = os.environ if environ is None else environ
        values = {name: parse(env[var]) for name, (var, parse) in _ENV.items() if var in env}
        values.update({name: value for name, value in overrides.items() if value is not None})
        return cls(**values)

    @property
    def voices_dir(self) -> Path:
        return self.data_dir / "voices"

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / ".sleng" / "jobs"

    def resolved_web_dist(self) -> Path | None:
        """The built UI to serve: the explicit setting, else ./web/dist if it exists."""
        candidate = self.web_dist or self.data_dir / "web" / "dist"
        return candidate if (candidate / "index.html").is_file() else None
