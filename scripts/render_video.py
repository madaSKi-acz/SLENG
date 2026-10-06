"""Render an MP4 (animated background, waveform, progress bar, burned-in subtitles) with ffmpeg + libass."""
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

FONT_DIR = Path(__file__).parent / "fonts"
DEFAULT_FAMILY = "Kantumruy Pro"
ACCENTS = {  # name -> (r, g, b)
    "blue": (91, 140, 255), "gold": (245, 185, 66), "green": (52, 211, 153),
    "pink": (244, 114, 182), "white": (235, 238, 245),
}
THEMES = ("plain", "gradient", "studio")


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


def find_fonts(font=None, font_name=None):
    """Return ([font files], family). An explicit --font replaces the bundled Kantumruy Pro."""
    if font:
        return [font], font_name or font_family(font) or Path(font).stem
    files = sorted(str(p) for p in FONT_DIR.glob("*.ttf"))
    return files, font_name or DEFAULT_FAMILY


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _hex(rgb):
    return "0x%02X%02X%02X" % rgb


def render_mp4(wav_bytes, ass_text, width, height, duration, font_files, out_path,
               theme="studio", accent="blue", progress=True):
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(f"ffmpeg not found. Install it with: {sys.executable} -m pip install imageio-ffmpeg")
    theme = theme if theme in THEMES else "studio"
    rgb = ACCENTS.get(accent, ACCENTS["blue"])
    total = duration + 0.3
    W, H = width, height
    base = (8, 10, 20)

    if theme == "plain":
        src = f"color=c=black:s={W}x{H}:r=25:d={total:.2f}"
    else:  # slowly moving two-tone gradient, tinted by the accent colour
        c0, c1 = _mix(base, rgb, 0.04), _mix(base, rgb, 0.30)
        src = (f"gradients=s={W}x{H}:r=25:d={total:.2f}:c0={_hex(c0)}:c1={_hex(c1)}:"
               f"x0=0:y0=0:x1={W}:y1={H}:speed=0.012")

    # filter graph: [0:v] background -> (+ waveform) -> (+ progress bar) -> subtitles
    chain, last = [], "[0:v]"
    if theme == "studio":
        wh = int(H * 0.16)
        chain.append(f"[1:a]showwaves=s={W}x{wh}:mode=cline:rate=25:scale=sqrt:colors={_hex(rgb)},"
                     f"format=rgba,colorkey=black:0.12:0.2[wv]")
        chain.append(f"{last}[wv]overlay=0:{int(H * 0.80)}:format=auto[v1]")
        last = "[v1]"
    if progress and theme != "plain":
        bar = max(4, H // 120)
        chain.append(f"color=c={_hex(rgb)}:s={W}x{bar}:r=25[bar]")
        chain.append(f"color=c=white@0.10:s={W}x{bar}:r=25,format=rgba[track]")
        chain.append(f"{last}[track]overlay=0:{H - bar}:format=auto[v2]")
        chain.append(f"[v2][bar]overlay=x='-w+w*t/{total:.2f}':y={H - bar}:format=auto[v3]")
        last = "[v3]"

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "audio.wav").write_bytes(wav_bytes)
        if ass_text:
            (tmp / "subs.ass").write_text(ass_text, encoding="utf-8")
            (tmp / "fonts").mkdir()
            for f in font_files:
                shutil.copy(f, tmp / "fonts" / Path(f).name)
            chain.append(f"{last}ass=subs.ass:fontsdir=fonts[vout]")
            last = "[vout]"
        if last == "[0:v]":
            chain.append("[0:v]null[vout]")
            last = "[vout]"
        cmd = [ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i", src, "-i", "audio.wav",
               "-filter_complex", ";".join(chain), "-map", last, "-map", "1:a",
               "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "out.mp4"]
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0 or not (tmp / "out.mp4").exists():
            raise RuntimeError("ffmpeg failed: " + (r.stderr or "")[-700:])
        shutil.move(str(tmp / "out.mp4"), out_path)
