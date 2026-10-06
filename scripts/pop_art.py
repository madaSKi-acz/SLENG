"""Cute, modern video art drawn from code (original - no stock assets, no national symbols).

Every video gets a new random layout from a seed:
  * a soft mesh gradient (big blurred colour blobs) with light film grain
  * Y2K-style decorations: rings, squiggles, dot grids, plus signs
  * sticker sprites (hearts, stars, sparkles, smileys, daisies, clouds, planets) that
    float and wobble around the edges, keeping the centre clear for captions
  * a frosted-glass pill that sits behind the voice bars
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PALETTES = {
    # name: (mesh colours, sticker colours)
    "candy": ([(255, 182, 213), (203, 170, 255), (160, 210, 255), (255, 214, 236)],
              [(255, 92, 170), (255, 205, 0), (90, 180, 255), (160, 110, 255), (255, 130, 90)]),
    "mint": ([(178, 245, 220), (255, 245, 170), (255, 205, 178), (190, 230, 255)],
             [(20, 190, 140), (255, 160, 40), (255, 95, 135), (80, 140, 255), (255, 210, 0)]),
    "sunset": ([(255, 170, 110), (255, 120, 160), (160, 110, 255), (255, 210, 140)],
               [(255, 225, 70), (255, 70, 115), (110, 80, 255), (50, 210, 190), (255, 255, 255)]),
    "night": ([(26, 20, 64), (128, 44, 178), (32, 96, 182), (76, 32, 140)],
              [(255, 80, 200), (70, 235, 255), (185, 255, 70), (255, 215, 50), (175, 125, 255)]),
}
SS = 2  # supersampling for smooth edges
INK = (34, 26, 48)  # dark outline / face colour


def _rgba(rgb, a=255):
    return (*rgb, int(a))


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


# ---------------------------------------------------------------- background
def background(width, height, palette="candy", seed=0):
    mesh, stick = PALETTES.get(palette, PALETTES["candy"])
    rng = random.Random(seed)
    W, H = width, height
    # mesh gradient: base colour + big blurred blobs
    img = Image.new("RGB", (W, H), mesh[0])
    blobs = Image.new("RGB", (W, H), mesh[0])
    d = ImageDraw.Draw(blobs)
    for i in range(6):
        c = mesh[(i + 1) % len(mesh)] if i < 4 else rng.choice(mesh)
        r = max(W, H) * rng.uniform(0.25, 0.45)
        x, y = rng.uniform(-0.1, 1.1) * W, rng.uniform(-0.1, 1.1) * H
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    img = blobs.filter(ImageFilter.GaussianBlur(max(W, H) * 0.12))

    deco = Image.new("RGBA", (W * SS, H * SS))
    dd = ImageDraw.Draw(deco)
    dark = palette == "night"
    line = (255, 255, 255) if not dark else (200, 190, 255)
    m = min(W, H) * SS
    # rings
    for _ in range(rng.randint(2, 4)):
        r = m * rng.uniform(0.08, 0.22)
        x, y = rng.uniform(0, W * SS), rng.uniform(0, H * SS)
        dd.ellipse([x - r, y - r, x + r, y + r], outline=_rgba(line, 110), width=int(m * 0.006))
    # squiggles
    for _ in range(rng.randint(2, 3)):
        x0, y0 = rng.uniform(0, W * SS), rng.uniform(0, H * SS)
        ln, amp, ph = m * rng.uniform(0.2, 0.4), m * rng.uniform(0.015, 0.03), rng.uniform(0, 6)
        ang = rng.uniform(-0.6, 0.6)
        pts = []
        for i in range(60):
            u = i / 59 * ln
            v = amp * math.sin(u / (m * 0.03) + ph)
            pts.append((x0 + u * math.cos(ang) - v * math.sin(ang), y0 + u * math.sin(ang) + v * math.cos(ang)))
        dd.line(pts, fill=_rgba(rng.choice(stick), 150), width=int(m * 0.008), joint="curve")
    # dot grids
    for _ in range(rng.randint(1, 2)):
        x0, y0, gap = rng.uniform(0, W * SS * 0.8), rng.uniform(0, H * SS * 0.8), m * 0.025
        r = m * 0.004
        for i in range(6):
            for j in range(4):
                cx, cy = x0 + i * gap, y0 + j * gap
                dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_rgba(line, 140))
    # plus signs
    for _ in range(rng.randint(4, 8)):
        cx, cy, s = rng.uniform(0, W * SS), rng.uniform(0, H * SS), m * 0.012
        col = _rgba(line, 160)
        dd.line([(cx - s, cy), (cx + s, cy)], fill=col, width=int(m * 0.004))
        dd.line([(cx, cy - s), (cx, cy + s)], fill=col, width=int(m * 0.004))
    img = img.convert("RGBA")
    img.alpha_composite(deco.resize((W, H), Image.LANCZOS))

    # film grain
    nrng = np.random.default_rng(seed)
    grain = nrng.normal(0, 6 if not dark else 5, (H, W, 1)).astype(np.float32)
    arr = np.clip(np.asarray(img.convert("RGB"), np.float32) + grain, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


# ---------------------------------------------------------------- stickers
def _heart(s):
    pts = []
    for i in range(80):
        t = i / 80 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((s / 2 + x * s / 38, s * 0.47 + y * s / 38))
    return lambda d, col: d.polygon(pts, fill=col)


def _star(s, points=5, inner=0.45):
    c, R = s / 2, s * 0.46
    pts = [(c + (R if i % 2 == 0 else R * inner) * math.sin(i * math.pi / points),
            c - (R if i % 2 == 0 else R * inner) * math.cos(i * math.pi / points)) for i in range(points * 2)]
    return lambda d, col: d.polygon(pts, fill=col)


def _sparkle(s):
    c, R, k = s / 2, s * 0.46, s * 0.1
    pts = []
    for i in range(4):  # concave 4-point star
        a = i * math.pi / 2
        pts.append((c + R * math.sin(a), c - R * math.cos(a)))
        a2 = a + math.pi / 4
        pts.append((c + k * math.sin(a2), c - k * math.cos(a2)))
    return lambda d, col: d.polygon(pts, fill=col)


def _circle(s, r=0.44):
    return lambda d, col: d.ellipse([s * (0.5 - r), s * (0.5 - r), s * (0.5 + r), s * (0.5 + r)], fill=col)


def _cloud(s):
    def draw(d, col):
        for cx, cy, r in [(0.3, 0.58, 0.18), (0.5, 0.45, 0.24), (0.7, 0.56, 0.19), (0.5, 0.62, 0.18)]:
            d.ellipse([s * (cx - r), s * (cy - r), s * (cx + r), s * (cy + r)], fill=col)
        d.rounded_rectangle([s * 0.14, s * 0.55, s * 0.86, s * 0.76], radius=s * 0.1, fill=col)
    return draw


def _daisy(s, n=8):
    def draw(d, col):
        c = s / 2
        for i in range(n):
            a = i * 2 * math.pi / n
            px, py, r = c + math.cos(a) * s * 0.26, c + math.sin(a) * s * 0.26, s * 0.17
            d.ellipse([px - r, py - r, px + r, py + r], fill=col)
    return draw


def _planet(s):
    def draw(d, col):
        d.ellipse([s * 0.27, s * 0.27, s * 0.73, s * 0.73], fill=col)
        d.ellipse([s * 0.06, s * 0.42, s * 0.94, s * 0.62], outline=col, width=int(s * 0.06))
    return draw


def _sticker(size, shape, color, detail=None, border=True):
    """Shape filled with `color`, white sticker border, soft drop shadow, optional face/centre details."""
    S = size * SS
    pad = int(S * 0.12)
    full = S + pad * 2
    mask = Image.new("L", (full, full))
    md = ImageDraw.Draw(mask)
    md_off = Image.new("L", (S, S))
    shape(ImageDraw.Draw(md_off), 255)
    mask.paste(md_off, (pad, pad))
    out = Image.new("RGBA", (full, full))
    if border:
        bw = max(3, int(S * 0.045)) | 1
        outline = mask.filter(ImageFilter.MaxFilter(bw * 2 + 1)) if bw * 2 + 1 <= 31 else mask.filter(ImageFilter.MaxFilter(31))
        shadow = outline.filter(ImageFilter.GaussianBlur(S * 0.03))
        sh = Image.new("RGBA", (full, full), _rgba(INK, 0))
        sh.putalpha(shadow.point(lambda v: v * 0.35))
        out.alpha_composite(sh, (int(S * 0.02), int(S * 0.035)))
        white = Image.new("RGBA", (full, full), (255, 255, 255, 255))
        white.putalpha(outline)
        out.alpha_composite(white)
    fill = Image.new("RGBA", (full, full), _rgba(color))
    fill.putalpha(mask)
    out.alpha_composite(fill)
    if detail:
        det = Image.new("RGBA", (S, S))
        detail(ImageDraw.Draw(det), S)
        out.alpha_composite(det, (pad, pad))
    final = size + int(size * 0.24)
    return out.resize((final, final), Image.LANCZOS)


def _face(d, S):  # smiley details
    for ex in (0.38, 0.62):
        d.ellipse([S * (ex - 0.04), S * 0.36, S * (ex + 0.04), S * 0.48], fill=_rgba(INK))
    d.arc([S * 0.3, S * 0.38, S * 0.7, S * 0.7], start=20, end=160, fill=_rgba(INK), width=int(S * 0.045))
    for cx in (0.27, 0.73):  # blush
        d.ellipse([S * (cx - 0.06), S * 0.52, S * (cx + 0.06), S * 0.58], fill=(255, 120, 150, 140))


def _daisy_centre(color):
    def draw(d, S):
        d.ellipse([S * 0.36, S * 0.36, S * 0.64, S * 0.64], fill=_rgba(color))
    return draw


def make_sticker(kind, size, colors, rng):
    col = rng.choice(colors)
    if kind == "heart":
        return _sticker(size, _heart(size * SS), col)
    if kind == "star":
        return _sticker(size, _star(size * SS), col)
    if kind == "sparkle":
        return _sticker(size, _sparkle(size * SS), col, border=False)
    if kind == "smiley":
        return _sticker(size, _circle(size * SS), (255, 214, 40), _face)
    if kind == "daisy":
        return _sticker(size, _daisy(size * SS), (255, 255, 255), _daisy_centre((255, 196, 30)))
    if kind == "cloud":
        return _sticker(size, _cloud(size * SS), (255, 255, 255))
    return _sticker(size, _planet(size * SS), col)


def stickers(width, height, palette="candy", seed=0, count=10):
    """[(RGBA image, x_expr, y_expr)] - stickers placed around the edges, bobbing and swaying."""
    _, colors = PALETTES.get(palette, PALETTES["candy"])
    rng = random.Random(seed + 7)
    m = min(width, height)
    kinds = ["heart", "star", "sparkle", "smiley", "daisy", "cloud", "planet"]
    rng.shuffle(kinds)
    out, placed = [], []
    for i in range(count):
        kind = kinds[i % len(kinds)] if i < len(kinds) else rng.choice(kinds)
        size = int(m * (rng.uniform(0.07, 0.12) if kind != "sparkle" else rng.uniform(0.04, 0.07)))
        img = make_sticker(kind, size, colors, rng)
        # place on a ring around the centre so captions stay readable
        aspect = width / height
        for _ in range(200):  # keep clear of captions (centre), voice bars (bottom centre) and each other
            x, y = rng.uniform(0.05, 0.95), rng.uniform(0.07, 0.9)
            in_caption = abs(x - 0.5) < 0.32 and abs(y - 0.45) < 0.2
            in_bars = abs(x - 0.5) < 0.34 and y > 0.74
            crowded = any(math.hypot((x - px) * aspect, y - py) < 0.16 for px, py in placed)
            if not (in_caption or in_bars or crowded):
                break
        placed.append((x, y))
        bob, sway = rng.uniform(0.008, 0.02), rng.uniform(0.004, 0.012)
        f1, f2, p1, p2 = rng.uniform(0.5, 1.1), rng.uniform(0.3, 0.8), rng.uniform(0, 6.3), rng.uniform(0, 6.3)
        xe = f"W*({x:.3f}+{sway:.3f}*sin(t*{f2:.2f}+{p2:.2f}))-w/2"
        ye = f"H*({y:.3f}+{bob:.3f}*sin(t*{f1:.2f}+{p1:.2f}))-h/2"
        out.append((img, xe, ye))
    return out


def glass_pill(width, height, dark=False):
    """Frosted rounded pill that sits behind the voice bars."""
    S = SS
    img = Image.new("RGBA", (width * S, height * S))
    d = ImageDraw.Draw(img)
    fill = (255, 255, 255, 70) if not dark else (255, 255, 255, 34)
    d.rounded_rectangle([0, 0, width * S - 1, height * S - 1], radius=height * S / 2, fill=fill,
                        outline=(255, 255, 255, 150 if not dark else 80), width=2 * S)
    return img.resize((width, height), Image.LANCZOS)
