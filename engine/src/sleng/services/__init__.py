"""
Purpose:  Use cases: what callers can ask the engine to do (speak, export, render, clone, jobs).
Layer:    sleng.services
Exports:  SpeechService, ExportService, VideoService, VoiceService, JobManager, Narration,
          CloneRequest, JobView, JobStatus
Depends:  sleng.voices, sleng.cloning, sleng.media, sleng.audio, sleng.text, sleng.domain
Notes:    Services take and return domain objects only; adapters translate HTTP/CLI around them.
"""

from sleng.services.exports import ExportService
from sleng.services.jobs import JobManager, JobStatus, JobView
from sleng.services.speech import Narration, SpeechService
from sleng.services.video import VideoService
from sleng.services.voices import CloneRequest, VoiceService

__all__ = [
    "CloneRequest",
    "ExportService",
    "JobManager",
    "JobStatus",
    "JobView",
    "Narration",
    "SpeechService",
    "VideoService",
    "VoiceService",
]
