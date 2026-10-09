"""
Purpose:  Errors the engine raises on purpose; adapters map them to exit codes / HTTP statuses.
Layer:    sleng.domain (pure)
Exports:  SlengError and its subclasses
Depends:  nothing
Notes:    Messages are shown to users as-is, so write them as plain, actionable sentences.
"""


class SlengError(Exception):
    """Base class for every error the engine raises on purpose."""


class InvalidInputError(SlengError):
    """The caller sent something unusable (empty text, unreadable clip, unknown option)."""


class NotFoundError(SlengError):
    """A voice, job or file that does not exist."""


class ConflictError(SlengError):
    """The request is valid but the resource is not in the right state (job still running)."""


class DependencyError(SlengError):
    """An optional package or binary (ffmpeg, torch, edge-tts, OpenVoice) is missing."""


class ExternalServiceError(SlengError):
    """A remote service (Microsoft Edge TTS) failed or returned nothing."""
