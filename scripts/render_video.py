"""Render an MP4 (animated background, waveform, progress bar, burned-in subtitles) with ffmpeg + libass."""
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

FONT_DIR = Path(__file__).parent / "fonts"
DEFAULT_FAMILY = "Kantumruy Pro"
PALETTES = {  # name -> three colours used for the glow orbs and progress bar
    "gemini": ((66, 133, 244), (155, 114, 203), (217, 101, 112)),
    "blue": ((91, 140, 255), (130, 100, 255), (60, 200, 255)),
    "gold": ((245, 185, 66), (255, 130, 60), (255, 220, 120)),
    "green": ((52, 211, 153), (60, 170, 255), (150, 230, 120)),
    "pink": ((244, 114, 182), (180, 100, 255), (255, 150, 120)),
    "white": ((235, 238, 245), (180, 190, 210), (140, 150, 170)),
}
ACCENTS = {k: v[0] for k, v in PALETTES.items()}  # main accent colour per palette
BASE_BG = (19, 19, 20)  # near-black, like Gemini's dark theme
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


def _hex(rgb):
    return "0x%02X%02X%02X" % tuple(rgb)


def _write_png(path, rgba):
    """Minimal RGBA PNG writer (numpy array HxWx4 uint8) - avoids needing Pillow."""
    import zlib

    import numpy as np

    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 3)) + chunk(b"IEND", b""))


def _orb_png(path, size, rgb, strength=0.55):
    """Soft round glow: constant colour, alpha falls off like a gaussian."""
    import numpy as np

    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    r2 = ((x - size / 2) ** 2 + (y - size / 2) ** 2) / (size / 2) ** 2
    a = (np.exp(-r2 * 3.2) * strength * 255).astype(np.uint8)
    img = np.zeros((size, size, 4), dtype=np.uint8)
    img[..., :3] = rgb
    img[..., 3] = a
    _write_png(path, img)


def _bar_png(path, width, height, colors):
    """Horizontal gradient bar through the palette colours."""
    import numpy as np

    t = np.linspace(0, 1, width, dtype=np.float32)
    stops = np.linspace(0, 1, len(colors))
    img = np.zeros((height, width, 4), dtype=np.uint8)
    for c in range(3):
        img[..., c] = np.interp(t, stops, [col[c] for col in colors]).astype(np.uint8)[None, :]
    img[..., 3] = 255
    _write_png(path, img)


def _envelope(wav_bytes, fps=25, step=0.01):
    """Loudness envelope of the voice (0..1), sampled every `step` seconds."""
    import io

    import numpy as np
    import scipy.io.wavfile as wavfile

    sr, x = wavfile.read(io.BytesIO(wav_bytes))
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = max(1, int(sr * step))
    n = len(x) // hop
    if n == 0:
        return np.zeros(1, dtype=np.float32)
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    ref = np.percentile(rms[rms > 0], 95) if (rms > 0).any() else 1.0
    env = np.clip(rms / max(ref, 1e-6), 0, 1) ** 0.6
    out, v = np.empty_like(env), 0.0  # fast attack, slow release
    for i, e in enumerate(env):
        v = e if e > v else v * 0.88 + e * 0.12
        out[i] = v
    return out


def _viz_frames(env, total, bw, bh, pal, fps=25, step=0.01, bars=31):
    """Yield RGBA frames: rounded bars, loudness ripples out from the centre, dots when silent."""
    import numpy as np

    slot = bw / bars
    barw = max(4, int(slot * 0.55))
    cols = np.arange(bw)
    idx = (cols / slot).astype(int).clip(0, bars - 1)
    inside = (cols - idx * slot - (slot - barw) / 2)
    valid = (inside >= 0) & (inside < barw)
    dist = np.abs(idx - bars // 2)  # 0 at the centre bar
    # colour per column: gradient through the palette, left -> right
    t = cols / max(bw - 1, 1)
    stops = np.linspace(0, 1, len(pal))
    rgb = np.stack([np.interp(t, stops, [c[k] for c in pal]) for k in range(3)], axis=1).astype(np.uint8)
    yy = np.abs(np.arange(bh)[:, None] - (bh - 1) / 2)
    frame = np.zeros((bh, bw, 4), dtype=np.uint8)
    frame[..., :3] = rgb[None, :, :]
    taper = 1 - (dist / (bars // 2 + 1)) ** 2 * 0.55  # outer bars a little shorter
    for f in range(int(total * fps) + 1):
        now = f / fps
        lag = (now - dist * 0.045) / step  # outer bars show slightly older loudness
        e = env[np.clip(lag.astype(int), 0, len(env) - 1)] * (lag >= 0)
        h = np.maximum(barw, e * taper * bh)  # never smaller than a dot
        half = h / 2
        a = np.clip(half[None, :] - yy + 1, 0, 1)  # 1px soft edge
        # round the bar ends: shrink the top/bottom corners with a circle of radius barw/2
        r = barw / 2
        cx = inside - barw / 2 + 0.5
        edge = np.sqrt(np.maximum(r * r - cx * cx, 0))  # half-height of the cap at this column
        cap = np.clip(yy - (half[None, :] - r), 0, None)
        a = np.where(cap > 0, np.clip(edge[None, :] - cap + 1, 0, 1) * (half[None, :] - yy + 1 > 0), a)
        frame[..., 3] = (a * valid[None, :] * 235).astype(np.uint8)
        yield frame.tobytes()


def render_mp4(wav_bytes, ass_text, width, height, duration, font_files, out_path,
               theme="studio", accent="gemini", progress=True):
    ff = find_ffmpeg()
    if not ff:
        raise RuntimeError(f"ffmpeg not found. Install it with: {sys.executable} -m pip install imageio-ffmpeg")
    theme = theme if theme in THEMES else "studio"
    pal = PALETTES.get(accent, PALETTES["gemini"])
    total = duration + 0.3
    W, H = width, height
    even = lambda v: int(v) // 2 * 2

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "audio.wav").write_bytes(wav_bytes)
        inputs = ["-f", "lavfi", "-i", f"color=c={_hex(BASE_BG)}:s={W}x{H}:r=25:d={total:.2f}", "-i", "audio.wav"]
        chain, last, n_in = [], "[0:v]", 2

        if theme != "plain":  # three slowly drifting glow orbs on the dark base
            size = even(max(W, H) * 0.95)
            motion = [  # centre x, centre y (fractions of the frame), drift speed/phase
                ("0.14+0.10*sin(t*0.35)", "0.18+0.08*cos(t*0.28)"),
                ("0.86+0.08*sin(t*0.30+2)", "0.28+0.10*sin(t*0.22+1)"),
                ("0.52+0.12*sin(t*0.25+4)", "1.02+0.06*cos(t*0.33)"),
            ]
            chain.append(f"{last}format=rgba[b0]")
            last = "[b0]"
            for i, (rgb, (mx, my)) in enumerate(zip(pal, motion), 1):
                _orb_png(tmp / f"orb{i}.png", size, rgb, 0.60 if i < 3 else 0.50)
                inputs += ["-loop", "1", "-framerate", "25", "-i", f"orb{i}.png"]
                chain.append(f"{last}[{n_in}:v]overlay=x='W*({mx})-w/2':y='H*({my})-h/2':format=auto[b{i}]")
                last, n_in = f"[b{i}]", n_in + 1

        viz = None
        if theme == "studio":  # Gemini-Live-style voice bars, fed to ffmpeg as raw frames on stdin
            bw, bh = even(min(W, H) * 0.62), even(min(W, H) * 0.13)
            viz = (_envelope(wav_bytes), bw, bh)
            inputs += ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{bw}x{bh}", "-framerate", "25", "-i", "pipe:0"]
            chain.append(f"[{n_in}:v]split[vz][vzg];[vzg]gblur=sigma={max(4, bh // 10)}[glow];[glow][vz]overlay=format=auto[eq]")
            chain.append(f"{last}[eq]overlay=x=(W-w)/2:y=H-h-{int(H * 0.07)}:format=auto[v1]")
            last, n_in = "[v1]", n_in + 1

        if progress and theme != "plain":  # thin gradient bar that grows with the audio
            bar = max(4, H // 140)
            _bar_png(tmp / "bar.png", W, bar, pal)
            inputs += ["-loop", "1", "-framerate", "25", "-i", "bar.png"]
            chain.append(f"color=c=white@0.10:s={W}x{bar}:r=25,format=rgba[track]")
            chain.append(f"{last}[track]overlay=0:{H - bar}:format=auto[v2]")
            chain.append(f"[v2][{n_in}:v]overlay=x='-w+w*t/{total:.2f}':y={H - bar}:format=auto[v3]")
            last, n_in = "[v3]", n_in + 1

        if ass_text:
            (tmp / "subs.ass").write_text(ass_text, encoding="utf-8")
            (tmp / "fonts").mkdir()
            for f in font_files:
                shutil.copy(f, tmp / "fonts" / Path(f).name)
            chain.append(f"{last}ass=subs.ass:fontsdir=fonts[vout]")
            last = "[vout]"
        else:
            chain.append(f"{last}null[vout]")
            last = "[vout]"

        cmd = [ff, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chain), "-map", last, "-map", "1:a",
               "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "out.mp4"]
        with open(tmp / "ffmpeg.log", "w+") as log:
            proc = subprocess.Popen(cmd, cwd=tmp, stdin=subprocess.PIPE if viz else subprocess.DEVNULL, stderr=log)
            if viz:
                env, bw, bh = viz
                try:
                    for fr in _viz_frames(env, total, bw, bh, pal):
                        proc.stdin.write(fr)
                except BrokenPipeError:
                    pass
                finally:
                    try:
                        proc.stdin.close()
                    except BrokenPipeError:
                        pass
            code = proc.wait()
            log.seek(0)
            err = log.read()
        if code != 0 or not (tmp / "out.mp4").exists():
            raise RuntimeError("ffmpeg failed: " + err[-700:])
        shutil.move(str(tmp / "out.mp4"), out_path)
