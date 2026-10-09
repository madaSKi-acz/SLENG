"""
Purpose:  What each `sleng` command does: build the engine, call one service, print or save.
Layer:    sleng.adapters.cli
Exports:  serve, speak, split, video, voices, openapi
Depends:  sleng.container, sleng.config, sleng.domain, sleng.infra.deps (uvicorn, fastapi)
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any

from sleng.config import Settings
from sleng.container import Sleng
from sleng.domain import (
    CleanupLevel,
    InvalidInputError,
    NarrationRequest,
    PauseOptions,
    Script,
    SpeechOptions,
    VideoOptions,
    VideoRequest,
    VideoTheme,
)
from sleng.infra.deps import require

TITLE_CARD_SECONDS = 2.6
API_EXTRA = '"sleng[api]"'


def serve(args: argparse.Namespace) -> int:
    uvicorn = require("uvicorn", API_EXTRA)
    require("fastapi", API_EXTRA)
    from sleng.adapters.http import create_app

    web_dist = Path(args.web_dist) if args.web_dist else None
    engine = Sleng(_settings(args, web_dist=web_dist))
    url = f"http://{args.host}:{args.port}"
    print(f"SLENG engine at {url}  (API docs: {url}/api/docs; Ctrl+C stops)", flush=True)
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(create_app(engine), host=args.host, port=args.port, log_level="info")
    return 0


def speak(args: argparse.Namespace) -> int:
    engine = Sleng(_settings(args))
    request = _narration(args)
    if args.format == "zip":
        data = engine.exports.zip(request.script, request.speech)
    elif args.format == "srt":
        data = engine.exports.srt(request).encode("utf-8")
    else:
        data = engine.exports.wav(request)
    Path(args.out).write_bytes(data)
    print(f"Saved {args.out}")
    return 0


def split(args: argparse.Namespace) -> int:
    engine = Sleng(_settings(args))
    for number, chunk in enumerate(engine.speech.split(_read_text(args), args.max_chars), 1):
        print(f"{number:>4} {chunk.pause.value:<9} {chunk.display}")
    return 0


def video(args: argparse.Namespace) -> int:
    engine = Sleng(_settings(args))
    request = VideoRequest(_narration(args), _video_options(args))
    seed = engine.video.render(request, Path(args.out), _print_progress)
    print(f"\nSaved {args.out} (design #{seed}; pass --seed {seed} to recreate it)")
    return 0


def voices(args: argparse.Namespace) -> int:
    for info in Sleng(_settings(args)).voices.voices():
        print(f"{info.id:<28} {info.name:<16} {info.source.value}")
    return 0


def openapi(args: argparse.Namespace) -> int:
    require("fastapi", API_EXTRA)
    from sleng.adapters.http import create_app

    schema = create_app(Sleng(_settings(args))).openapi()
    text = json.dumps(schema, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


def _settings(args: argparse.Namespace, **extra: Any) -> Settings:
    return Settings.from_env(
        data_dir=Path(args.data_dir) if args.data_dir else None,
        device=args.device,
        fake=args.fake or None,
        font_path=Path(args.font) if args.font else None,
        font_family=args.font_name,
        **extra,
    )


def _read_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return str(args.text)
    if args.file == "-":
        return sys.stdin.read()
    return Path(args.file).read_text(encoding="utf-8")


def _narration(args: argparse.Namespace) -> NarrationRequest:
    script = Script(text=_read_text(args), max_chars=args.max_chars)
    speech = SpeechOptions(args.voice, args.speed, CleanupLevel(args.cleanup))
    pauses = PauseOptions(args.pause, args.para_pause, smart=not args.plain_merge)
    return NarrationRequest(script, speech, pauses)


def _video_options(args: argparse.Namespace) -> VideoOptions:
    width, height = _size(args.size)
    return VideoOptions(
        width=width,
        height=height,
        theme=VideoTheme(args.theme),
        palette=args.palette,
        title=args.title,
        intro_seconds=0.0 if args.no_title_card else TITLE_CARD_SECONDS,
        subtitles=not args.no_subtitles,
        karaoke=not args.no_karaoke,
        progress_bar=not args.no_progress,
        seed=args.seed,
    )


def _size(text: str) -> tuple[int, int]:
    try:
        width, height = (int(part) for part in text.lower().split("x"))
    except ValueError as err:
        raise InvalidInputError(f"Size must look like 1280x720, not {text!r}.") from err
    return width, height


def _print_progress(done: float) -> None:
    print(f"\rRendering {done:4.0%}", end="", flush=True)
