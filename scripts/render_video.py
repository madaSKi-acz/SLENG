"""Render a black-screen MP4 with burned-in running subtitles (needs ffmpeg with libass)."""
import glob
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# (file name pattern, family name used by ASS/libass)
KNOWN_FONTS = [
    ("C:/Windows/Fonts/LeelawUI.ttf", "Leelawadee UI"), ("C:/Windows/Fonts/leelawui.ttf", "Leelawadee UI"),
    ("C:/Windows/Fonts/KhmerUI.ttf", "Khmer UI"), ("C:/Windows/Fonts/khmerui.ttf", "Khmer UI"),
    ("/usr/share/fonts/**/NotoSansKhmer*.ttf", "Noto Sans Khmer"), ("/usr/share/fonts/**/NotoSerifKhmer*.ttf", "Noto Serif Khmer"),
    ("/Library/Fonts/**/Khmer*.ttf", None), ("/System/Library/Fonts/**/Khmer*.tt*", None),
]


def find_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def font_family(path):
    """Read the family name from a TTF/OTF 'name' table (no extra dependency)."""
    try:
        data = Path(path).read_bytes()
        n = struct.unpack(">H", data[4:6])[0]
        for i in range(n):
            tag, _, off, _ = struct.unpack(">4sIII", data[12 + 16 * i: 28 + 16 * i])
            if tag == b"name":
                count, str_off = struct.unpack(">HH", data[off + 2: off + 6])
                best = None
                for j in range(count):
                    pid, eid, _, nid, ln, so = struct.unpack(">HHHHHH", data[off + 6 + 12 * j: off + 18 + 12 * j])
                    if nid in (1, 16):
                        raw = data[off + str_off + so: off + str_off + so + ln]
                        txt = raw.decode("utf-16-be" if pid in (0, 3) else "latin-1", "ignore")
                        if txt and (best is None or nid == 16):
                            best = txt
                return best
    except Exception:
        pass
    return None


def find_font(font=None, font_name=None):
    """Return (path, family). Explicit `font` wins; otherwise search common Khmer fonts."""
    if font:
        return font, font_name or font_family(font) or Path(font).stem
    for pattern, family in KNOWN_FONTS:
        for hit in glob.glob(pattern, recursive=True):
            return hit, font_name or family or font_family(hit) or Path(hit).stem
    return None, None


def render_mp4(wav_bytes, ass_text, width, height, duration, font_path, out_path):
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(f"ffmpeg not found. Install it with: {sys.executable} -m pip install imageio-ffmpeg")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "audio.wav").write_bytes(wav_bytes)
        vf = []
        if ass_text:
            (tmp / "subs.ass").write_text(ass_text, encoding="utf-8")
            (tmp / "fonts").mkdir()
            if font_path:
                shutil.copy(font_path, tmp / "fonts" / Path(font_path).name)
            vf = ["-vf", "ass=subs.ass:fontsdir=fonts"]
        cmd = [ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r=25",
               "-i", "audio.wav", *vf, "-t", f"{duration + 0.3:.2f}",
               "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "23", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "out.mp4"]
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0 or not (tmp / "out.mp4").exists():
            raise RuntimeError("ffmpeg failed: " + (r.stderr or "")[-600:])
        shutil.move(str(tmp / "out.mp4"), out_path)
