"""
Purpose:  Argument parsing for `sleng`: serve | speak | split | video | voices | openapi.
Layer:    sleng.adapters.cli
Exports:  main, build_parser
Depends:  argparse, sleng.adapters.cli.commands, sleng.domain
Notes:    Engine options (--data-dir, --device, --fake, --font) work after every command.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import TypeAlias

from sleng.adapters.cli import commands
from sleng.domain import CleanupLevel, SlengError, VideoTheme

Commands: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"


def main(argv: list[str] | None = None) -> int:
    """Entry point of the `sleng` script; returns the process exit code."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        return int(args.handler(args))
    except SlengError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sleng", description="Khmer text-to-speech engine.")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    engine = _engine_options()
    _add_serve(subparsers, engine)
    _add_speak(subparsers, engine)
    _add_split(subparsers, engine)
    _add_video(subparsers, engine)
    _add_tools(subparsers, engine)
    return parser


def _engine_options() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    group = shared.add_argument_group("engine")
    group.add_argument("--data-dir", help="folder holding voices/ (default: current folder)")
    group.add_argument("--device", choices=["cpu", "cuda"], help="model device (default: auto)")
    group.add_argument("--fake", action="store_true", help="test tones instead of real voices")
    group.add_argument("--font", help="subtitle .ttf/.otf instead of the bundled Kantumruy Pro")
    group.add_argument("--font-name", help="font family name if it cannot be read from the file")
    return shared


def _add_serve(subparsers: Commands, engine: argparse.ArgumentParser) -> None:
    serve = subparsers.add_parser("serve", parents=[engine], help="run the HTTP API and the UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=7860)
    serve.add_argument("--no-browser", action="store_true", help="do not open a browser")
    serve.add_argument("--web-dist", help="built web UI folder (default: ./web/dist if present)")
    serve.set_defaults(handler=commands.serve)


def _add_speak(subparsers: Commands, engine: argparse.ArgumentParser) -> None:
    speak = subparsers.add_parser("speak", parents=[engine], help="text -> WAV, zip or SRT")
    _add_text_source(speak)
    _add_speech_options(speak)
    speak.add_argument("--format", choices=["wav", "zip", "srt"], default="wav")
    speak.add_argument("--out", required=True, help="output file")
    speak.set_defaults(handler=commands.speak)


def _add_split(subparsers: Commands, engine: argparse.ArgumentParser) -> None:
    split = subparsers.add_parser("split", parents=[engine], help="show how text is split")
    _add_text_source(split)
    split.add_argument("--max-chars", type=int, default=250)
    split.set_defaults(handler=commands.split)


def _add_video(subparsers: Commands, engine: argparse.ArgumentParser) -> None:
    video = subparsers.add_parser("video", parents=[engine], help="text -> MP4")
    _add_text_source(video)
    _add_speech_options(video)
    video.add_argument("--size", default="1280x720", help="1280x720, 1920x1080, 1080x1920, ...")
    video.add_argument("--theme", choices=[t.value for t in VideoTheme], default="studio")
    video.add_argument("--palette", default="gemini")
    video.add_argument("--title", default="")
    video.add_argument("--seed", type=int, help="design number to recreate a look")
    video.add_argument("--no-title-card", action="store_true")
    video.add_argument("--no-subtitles", action="store_true")
    video.add_argument("--no-karaoke", action="store_true")
    video.add_argument("--no-progress", action="store_true")
    video.add_argument("--out", required=True, help="output .mp4")
    video.set_defaults(handler=commands.video)


def _add_tools(subparsers: Commands, engine: argparse.ArgumentParser) -> None:
    voices = subparsers.add_parser("voices", parents=[engine], help="list available voices")
    voices.set_defaults(handler=commands.voices)
    schema = subparsers.add_parser("openapi", parents=[engine], help="print the API schema")
    schema.add_argument("--out", help="write to a file instead of stdout")
    schema.set_defaults(handler=commands.openapi)


def _add_text_source(parser: argparse.ArgumentParser) -> None:
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="the text itself")
    source.add_argument("--file", help="UTF-8 text file ('-' reads stdin)")


def _add_speech_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--voice", default="km-KH-SreymomNeural", help="see `sleng voices`")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--cleanup", choices=[c.value for c in CleanupLevel], default="light")
    parser.add_argument("--pause", type=float, default=0.2, help="seconds between sentences")
    parser.add_argument("--para-pause", type=float, default=0.6, help="between paragraphs")
    parser.add_argument("--plain-merge", action="store_true", help="no loudness matching")
    parser.add_argument("--max-chars", type=int, default=250, help="longest line, in characters")
