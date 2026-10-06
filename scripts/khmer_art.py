"""Procedurally drawn Khmer-style video art (original, generated from code - no stock assets).

Everything here is drawn with Pillow from simple shapes and a random seed:
  * a warm night-sky gradient with a glowing moon
  * kbach-inspired ornament bands (stylised flame/leaf motifs, diamonds, dots)
  * a skyline of stylised prasat towers and sugar palms
  * sprites (lotus flowers, petals, sparkles) that float across the video
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PALETTES = {
    #          sky top        sky bottom     gold            silhouette    moon glow      lotus
    "angkor": ((34, 8, 14), (96, 28, 22), (236, 184, 92), (18, 5, 8), (255, 176, 92), (242, 150, 160)),
    "lotus": ((8, 30, 38), (20, 74, 76), (240, 204, 128), (5, 18, 22), (255, 200, 205), (246, 140, 172)),
    "mekong": ((10, 14, 42), (34, 34, 88), (238, 198, 112), (6, 8, 24), (255, 214, 150), (222, 150, 206)),
}
SS = 2  # supersampling factor for smooth edges


def _rgba(rgb, a=255):
    return (*rgb, int(a))


def _gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img = (np.array(top, np.float32) * (1 - t) + np.array(bottom, np.float32) * t).repeat(w, axis=1)
    return Image.fromarray(img.astype(np.uint8), "RGB")


def _radial(w, h, cx, cy, radius, rgb, strength):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / radius
    a = np.clip(np.exp(-d * d * 2.2) * strength, 0, 1)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _kbach_leaf(cx, cy, s, flip=False, curl=1.0):
    """Outline of a stylised kbach flame/leaf: a swelling teardrop whose tip curls sideways."""
    pts_l, pts_r = [], []
    for i in range(25):
        t = i / 24
        width = s * 0.42 * math.sin(math.pi * min(1, t * 1.15)) * (1 - 0.55 * t)
        drift = curl * s * 0.32 * t ** 2.4
        y = -s * t
        pts_l.append((cx - width + drift, y))
        pts_r.append((cx + width * 0.8 + drift, y))
    pts = pts_l + pts_r[::-1]
    sign = 1 if flip else -1
    return [(x, cy - sign * y) for x, y in pts]


def _band(draw, w, y, h, gold, alpha, rng, flip):
    """One ornament band: a rule, a row of kbach leaves with alternating curl, diamonds and dots."""
    col = _rgba(gold, alpha)
    rule = y + (h - 2 * SS if flip else 2 * SS)
    draw.line([(0, rule), (w, rule)], fill=col, width=2 * SS)
    step = h * 1.25
    base = y + (h * 0.12 if flip else h * 0.88)
    k = 0
    x = step / 2 + rng.uniform(0, step / 2)
    while x < w + step:
        draw.polygon(_kbach_leaf(x, base, h * 0.72, flip=flip, curl=1 if k % 2 else -1), fill=col)
        mid = x + step / 2
        dy = h * 0.32
        cy = base + (dy if flip else -dy)
        r = h * 0.11
        draw.polygon([(mid, cy - r), (mid + r, cy), (mid, cy + r), (mid - r, cy)], fill=col)
        for dx in (-step * 0.32, step * 0.32):
            draw.ellipse([mid + dx - r * 0.35, cy - r * 0.35, mid + dx + r * 0.35, cy + r * 0.35], fill=col)
        x += step
        k += 1


def _prasat(draw, cx, ground, height, color):
    """Stylised Khmer temple tower: plinth, stepped tiers with side finials, lotus-bud top."""
    w = height * 0.42
    draw.rectangle([cx - w * 0.62, ground - height * 0.10, cx + w * 0.62, ground], fill=color)
    tiers = 6
    y = ground - height * 0.10
    for i in range(tiers):
        tw = w * (1 - i / (tiers + 1.2))
        th = height * 0.11
        draw.rounded_rectangle([cx - tw / 2, y - th, cx + tw / 2, y], radius=th * 0.25, fill=color)
        f = th * 0.55  # small flame finials at both corners of each tier
        for sx in (-1, 1):
            fx = cx + sx * tw / 2
            draw.polygon([(fx - f * 0.3, y - th), (fx + f * 0.3, y - th), (fx + sx * f * 0.15, y - th - f)], fill=color)
        y -= th * 0.92
    bud = w * 0.20
    draw.ellipse([cx - bud, y - bud * 2.0, cx + bud, y + bud * 0.3], fill=color)
    draw.polygon([(cx - bud * 0.3, y - bud * 1.6), (cx + bud * 0.3, y - bud * 1.6), (cx, y - bud * 3.4)], fill=color)


def _temple(draw, cx, ground, height, color, rng):
    """A temple group: gallery base with a tall central tower and smaller flanking towers."""
    gw = height * rng.uniform(1.3, 1.8)
    draw.rectangle([cx - gw / 2, ground - height * 0.09, cx + gw / 2, ground], fill=color)
    draw.rectangle([cx - gw * 0.42, ground - height * 0.15, cx + gw * 0.42, ground], fill=color)
    n = rng.choice([3, 5])
    offs = [0, -0.27, 0.27, -0.5, 0.5][:n]
    for i, o in sorted(enumerate(offs), key=lambda p: -abs(p[1])):  # back towers first
        scale = 1.0 if o == 0 else (0.78 if abs(o) < 0.3 else 0.62)
        _prasat(draw, cx + o * gw, ground - height * 0.12, height * scale, color)


def _sugar_palm(draw, x, ground, height, color, rng):
    """Cambodian sugar palm: tall thin trunk with a round fan crown."""
    lean = rng.uniform(-0.08, 0.08) * height
    top = (x + lean, ground - height)
    tw = max(2 * SS, height * 0.022)
    draw.polygon([(x - tw, ground), (x + tw, ground), (top[0] + tw * 0.6, top[1]), (top[0] - tw * 0.6, top[1])], fill=color)
    n = rng.randint(16, 22)
    for i in range(n):
        ang = math.radians(-180 + 180 * (i + 0.5) / n + rng.uniform(-4, 4))
        ln = height * rng.uniform(0.17, 0.24)
        ex, ey = top[0] + math.cos(ang) * ln, top[1] + math.sin(ang) * ln * 0.95
        nx, ny = -math.sin(ang), math.cos(ang)
        bw = height * 0.012
        draw.polygon([(top[0] + nx * bw, top[1] + ny * bw), (ex, ey), (top[0] - nx * bw, top[1] - ny * bw)], fill=color)
    for i in range(5):  # hanging leaves
        ang = math.radians(rng.uniform(20, 160))
        ln = height * rng.uniform(0.10, 0.16)
        draw.line([top, (top[0] + math.cos(ang) * ln, top[1] + math.sin(ang) * ln)], fill=color, width=int(tw))
    r = height * 0.03
    draw.ellipse([top[0] - r, top[1] - r * 0.4, top[0] + r, top[1] + r * 1.4], fill=color)


def background(width, height, palette="angkor", seed=0):
    """Return the still background (RGB PIL image) for the Khmer theme."""
    top, bottom, gold, dark, glow, _ = PALETTES.get(palette, PALETTES["angkor"])
    rng = random.Random(seed)
    W, H = width * SS, height * SS
    img = _gradient(W, H, top, bottom).convert("RGBA")

    # moon + glow, on a random side
    mx = W * rng.choice([rng.uniform(0.15, 0.3), rng.uniform(0.7, 0.85)])
    my = H * rng.uniform(0.18, 0.32)
    img.alpha_composite(_radial(W, H, mx, my, min(W, H) * 0.55, glow, 0.35))
    mr = min(W, H) * 0.075
    moon = Image.new("RGBA", (W, H))
    ImageDraw.Draw(moon).ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=_rgba(_mix(glow, (255, 245, 225), 0.6), 235))
    img.alpha_composite(moon.filter(ImageFilter.GaussianBlur(SS)))

    # faint stars
    stars = ImageDraw.Draw(img)
    for _ in range(int(W * H / (SS * SS) / 9000)):
        sx, sy, sr = rng.uniform(0, W), rng.uniform(0, H * 0.6), rng.uniform(0.5, 1.4) * SS
        stars.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=_rgba((255, 240, 210), rng.randint(60, 170)))

    # skyline: towers and palms in two depths (far = lighter, near = darker)
    ground = H * rng.uniform(0.86, 0.9)
    for depth, (col, scale) in enumerate([(_mix(dark, bottom, 0.45), 0.75), (dark, 1.0)]):
        layer = Image.new("RGBA", (W, H))
        d = ImageDraw.Draw(layer)
        g = ground - (H * 0.03 if depth == 0 else 0)
        d.rectangle([0, g, W, H], fill=_rgba(col))
        if depth == 0:  # distant single towers
            for _ in range(rng.randint(1, 2)):
                _prasat(d, rng.uniform(0.1, 0.9) * W, g + 2, H * rng.uniform(0.16, 0.22) * scale, _rgba(col))
        else:  # the main temple, off-centre so the subtitles stay readable
            tx = W * rng.choice([rng.uniform(0.22, 0.38), rng.uniform(0.62, 0.78)])
            _temple(d, tx, g + 2, H * rng.uniform(0.30, 0.38), _rgba(col), rng)
        for _ in range(rng.randint(3, 6)):
            _sugar_palm(d, rng.uniform(0, W), g + 2, H * rng.uniform(0.18, 0.32) * scale, _rgba(col), rng)
        img.alpha_composite(layer)

    # ornament bands top and bottom
    orn = Image.new("RGBA", (W, H))
    od = ImageDraw.Draw(orn)
    bh = min(W, H) * 0.052
    _band(od, W, H * 0.025, bh, gold, 150, rng, flip=True)
    _band(od, W, H - H * 0.025 - bh, bh, gold, 120, rng, flip=False)
    img.alpha_composite(orn)

    # gentle vignette
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    v = np.clip(((x / W - 0.5) ** 2 + (y / H - 0.5) ** 2) * 1.6, 0, 0.55)
    vig = np.zeros((H, W, 4), np.uint8)
    vig[..., 3] = (v * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(vig, "RGBA"))
    return img.resize((width, height), Image.LANCZOS).convert("RGB")


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _petal(cx, cy, length, width, angle):
    pts = []
    for i in range(30):
        t = i / 29 * math.pi
        px, py = math.sin(t) * width * (1 - 0.35 * (1 - math.cos(t)) / 2), -length * (1 - math.cos(t)) / 2
        pts.append((px, py))
    pts += [(-x, y) for x, y in pts[::-1]]
    c, s = math.cos(angle), math.sin(angle)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def lotus_sprite(size, palette="angkor", seed=0):
    """A lotus flower (RGBA PIL image)."""
    *_, gold, _, _, lotus = PALETTES.get(palette, PALETTES["angkor"])[:6]
    rng = random.Random(seed)
    S = size * SS
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    cx, cy = S / 2, S * 0.68
    light, deep = _mix(lotus, (255, 255, 255), 0.35), _mix(lotus, (120, 30, 60), 0.25)
    for ang, ln, wd, col in [(-1.15, 0.42, 0.13, deep), (1.15, 0.42, 0.13, deep), (-0.7, 0.5, 0.15, lotus),
                             (0.7, 0.5, 0.15, lotus), (-0.3, 0.56, 0.16, light), (0.3, 0.56, 0.16, light),
                             (0.0, 0.6, 0.17, _mix(light, (255, 255, 255), 0.3))]:
        d.polygon(_petal(cx, cy, S * ln, S * wd, ang + rng.uniform(-0.05, 0.05)), fill=_rgba(col, 235))
    d.ellipse([cx - S * 0.22, cy - S * 0.02, cx + S * 0.22, cy + S * 0.07], fill=_rgba(_mix(gold, (40, 90, 50), 0.55), 220))
    glow = img.filter(ImageFilter.GaussianBlur(S * 0.04))
    out = Image.new("RGBA", (S, S))
    out.alpha_composite(glow)
    out.alpha_composite(img)
    return out.resize((size, size), Image.LANCZOS)


def petal_sprite(size, palette="angkor", seed=0):
    lotus = PALETTES.get(palette, PALETTES["angkor"])[5]
    S = size * SS
    img = Image.new("RGBA", (S, S))
    ImageDraw.Draw(img).polygon(_petal(S / 2, S * 0.8, S * 0.6, S * 0.2, random.Random(seed).uniform(-0.6, 0.6)),
                                fill=_rgba(_mix(lotus, (255, 255, 255), 0.25), 200))
    return img.resize((size, size), Image.LANCZOS)


def sparkle_sprite(size, palette="angkor"):
    gold = PALETTES.get(palette, PALETTES["angkor"])[2]
    S = size * SS
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    c, r, k = S / 2, S * 0.45, S * 0.07
    d.polygon([(c, c - r), (c + k, c - k), (c + r, c), (c + k, c + k), (c, c + r), (c - k, c + k), (c - r, c), (c - k, c - k)],
              fill=_rgba(_mix(gold, (255, 255, 255), 0.5), 230))
    out = img.filter(ImageFilter.GaussianBlur(S * 0.05))
    out.alpha_composite(img)
    return out.resize((size, size), Image.LANCZOS)


def floaters(width, height, palette="angkor", seed=0, count=9):
    """Sprites + motion expressions for ffmpeg overlay: [(PIL image, x_expr, y_expr)]."""
    rng = random.Random(seed + 1)
    m = min(width, height)
    out = []
    for i in range(count):
        kind = rng.choices(["lotus", "petal", "sparkle"], weights=[3, 4, 3])[0]
        if kind == "lotus":
            size = int(m * rng.uniform(0.07, 0.11)) // 2 * 2
            spr = lotus_sprite(size, palette, seed + i)
        elif kind == "petal":
            size = int(m * rng.uniform(0.035, 0.06)) // 2 * 2
            spr = petal_sprite(size, palette, seed + i)
        else:
            size = int(m * rng.uniform(0.025, 0.045)) // 2 * 2
            spr = sparkle_sprite(size, palette)
        speed = rng.uniform(0.012, 0.035) * height  # px per second, drifting upward
        x0, amp, freq, ph = rng.uniform(0.05, 0.95), rng.uniform(0.01, 0.04), rng.uniform(0.2, 0.5), rng.uniform(0, 6.28)
        off = rng.uniform(0, height)
        x = f"W*{x0:.3f}+W*{amp:.3f}*sin(t*{freq:.2f}+{ph:.2f})-w/2"
        y = f"H-mod(t*{speed:.1f}+{off:.1f},H+h)"
        out.append((spr, x, y))
    return out
