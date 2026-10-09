"""
Purpose:  Composition root and public Python API: builds and wires every engine service once.
Layer:    sleng.container
Exports:  Sleng
Depends:  sleng.config, sleng.services, sleng.voices, sleng.cloning, sleng.media, sleng.infra
Notes:    Usage from any Python process:
              from sleng import Sleng
              from sleng.domain import NarrationRequest, Script, SpeechOptions
              engine = Sleng()
              wav = engine.exports.wav(NarrationRequest(Script(text="សួស្តី")))
"""

from __future__ import annotations

import logging
import threading

from sleng.audio.cleanup import VoiceCleaner
from sleng.cloning.converter import ToneConverter
from sleng.cloning.store import CloneStore
from sleng.cloning.voice import CloneKit
from sleng.config import Settings
from sleng.domain.voice import MMS
from sleng.infra.ffmpeg import Ffmpeg
from sleng.media.fonts import load_fonts
from sleng.media.renderer import VideoRenderer
from sleng.services.exports import ExportService
from sleng.services.jobs import JobManager
from sleng.services.speech import SpeechService
from sleng.services.video import VideoService
from sleng.services.voices import VoiceService
from sleng.voices.factory import VoiceFactory
from sleng.voices.registry import VoiceRegistry

log = logging.getLogger(__name__)
WARM_UP_TEXT = "ក"


class Sleng:
    """One engine per process. Thread-safe: share it between requests and threads."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        ffmpeg = Ffmpeg()
        clones = CloneKit(CloneStore(self.settings.voices_dir), ToneConverter(self.settings.device))
        factory = VoiceFactory(clones, self.settings.device, self.settings.fake)
        self.registry = VoiceRegistry(factory, clones.store, VoiceCleaner(ffmpeg))
        fonts = load_fonts(self.settings.font_path, self.settings.font_family)
        self.speech = SpeechService(self.registry)
        self.exports = ExportService(self.speech)
        self.video = VideoService(self.speech, VideoRenderer(ffmpeg, fonts), fonts)
        self.voices = VoiceService(self.registry, clones, ffmpeg)
        self.jobs = JobManager(self.settings.jobs_dir, workers=self.settings.job_workers)

    def warm_up(self) -> None:
        """Load the offline model in the background so the first request is fast."""
        if not self.settings.fake:
            threading.Thread(target=self._warm, name="sleng-warm-up", daemon=True).start()

    def close(self) -> None:
        self.jobs.shutdown()

    def _warm(self) -> None:
        try:
            self.registry.engine(MMS.id).synthesize(WARM_UP_TEXT)
        # Warm-up is optional: report and carry on (e.g. torch is not installed).
        except Exception as err:  # noqa: BLE001
            log.warning("Offline voice warm-up skipped: %s", err)
