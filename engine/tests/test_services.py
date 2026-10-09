"""
Purpose:  Engine services end-to-end with fake voices (no models, no network, no ffmpeg).
Layer:    engine tests
Depends:  sleng
"""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import pytest

from sleng.container import Sleng
from sleng.domain import (
    MMS,
    CleanupLevel,
    NarrationRequest,
    NotFoundError,
    Script,
    SpeechOptions,
)
from sleng.services.jobs import JobManager, JobStatus

RAW = SpeechOptions(voice=MMS.id, cleanup=CleanupLevel.OFF)


def test_wav_export_is_a_wav_file(engine: Sleng) -> None:
    data = engine.exports.wav(NarrationRequest(Script(text="សួស្តី។ អរគុណ។"), RAW))
    assert data[:4] == b"RIFF"


def test_zip_export_has_one_wav_per_line(engine: Sleng) -> None:
    data = engine.exports.zip(Script(text="ក។\nខ។"), RAW)
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert names == ["001.wav", "002.wav", "chunks.txt"]


def test_srt_export(engine: Sleng) -> None:
    srt = engine.exports.srt(NarrationRequest(Script(text="ក។ ខ។"), RAW))
    assert srt.startswith("1\n00:00:00,000 --> ")


def test_unknown_voice(engine: Sleng) -> None:
    with pytest.raises(NotFoundError):
        engine.speech.speak_line("ក", SpeechOptions(voice="nope", cleanup=CleanupLevel.OFF))


def test_builtin_voices_listed_first(engine: Sleng) -> None:
    assert [voice.id for voice in engine.voices.voices()][:3] == [
        "km-KH-SreymomNeural",
        "km-KH-PisethNeural",
        "mms",
    ]


def wait_for(manager: JobManager, job_id: str) -> JobStatus:
    for _ in range(200):
        status = manager.get(job_id).status
        if status in (JobStatus.DONE, JobStatus.FAILED):
            return status
        time.sleep(0.01)
    raise AssertionError("job did not finish")


def test_job_manager_success_and_failure(tmp_path: Path) -> None:
    manager = JobManager(tmp_path / "jobs")

    def write(path: Path, report: object) -> dict[str, object]:
        path.write_bytes(b"ok")
        return {"seed": 7}

    def boom(path: Path, report: object) -> dict[str, object]:
        raise RuntimeError("secret detail")

    good = manager.submit("test", "text/plain", ".txt", write)
    bad = manager.submit("test", "text/plain", ".txt", boom)
    assert wait_for(manager, good.id) is JobStatus.DONE
    assert manager.get(good.id).meta == {"seed": 7}
    assert manager.result(good.id)[0].read_bytes() == b"ok"
    assert wait_for(manager, bad.id) is JobStatus.FAILED
    assert "secret" not in (manager.get(bad.id).error or "")
    manager.shutdown()
