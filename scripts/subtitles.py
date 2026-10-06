"""Subtitle cues (SRT / ASS) from chunk texts and their audio timings."""
import re


def _fmt_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _fmt_ass(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def split_cue_text(text, max_chars=60):
    """Break text into short subtitle lines at sentence ends, then at spaces."""
    parts = [p.strip() for p in re.split(r"(?<=[។៕?!])", text) if p.strip()]
    out = []
    for part in parts:
        cur = ""
        for word in part.split(" "):
            if cur and len(cur) + 1 + len(word) > max_chars:
                out.append(cur)
                cur = word
            else:
                cur = f"{cur} {word}".strip()
        if cur:
            out.append(cur)
    return out


def make_cues(displays, spans, max_chars=60):
    """displays: chunk texts; spans: (start, end) seconds per chunk -> [(start, end, text)].
    A chunk's time is shared between its lines in proportion to their length."""
    cues = []
    for text, (a, b) in zip(displays, spans):
        lines = split_cue_text(text, max_chars)
        total = sum(len(x) for x in lines) or 1
        t = a
        for line in lines:
            d = (b - a) * len(line) / total
            cues.append((t, t + d, line))
            t += d
    return cues


def to_srt(cues):
    return "\n".join(f"{i}\n{_fmt_srt(a)} --> {_fmt_srt(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1))


def _bgr(rgb):
    """(r, g, b) -> ASS colour &HAABBGGRR (AA=00 opaque)."""
    r, g, b = rgb
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _karaoke(text, duration):
    """Spread the cue duration over its space-separated phrases (\\kf = smooth fill).
    Khmer has no spaces inside phrases, so splitting at spaces never breaks letter shaping."""
    words = text.split(" ")
    total = sum(len(w) for w in words) or 1
    cs_total = max(int(round(duration * 100)), len(words))
    out, used = [], 0
    for i, w in enumerate(words):
        cs = cs_total - used if i == len(words) - 1 else max(1, int(round(cs_total * len(w) / total)))
        used += cs
        out.append(f"{{\\kf{cs}}}{w}" + (" " if i < len(words) - 1 else ""))
    return "".join(out)


def to_ass(cues, width, height, font_name, font_size, accent=(255, 255, 255), karaoke=False, title="",
           duration=0.0, intro=0.0):
    """Modern caption look: white text on the dark scene with a soft shadow. With karaoke the
    not-yet-spoken words are dim grey and light up to white as they are spoken.
    If `intro` > 0 the title is shown as a big centred card for that many seconds."""
    esc = lambda t: t.replace("\\", "").replace("{", "(").replace("}", ")")
    margin = int(width * 0.08)
    white, dim = _bgr((255, 255, 255)), _bgr((128, 132, 138))
    primary, secondary = (white, dim) if karaoke else (white, white)
    outline = max(2, font_size // 16)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary},{secondary},&H70000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,5,{margin},{margin},{int(height * 0.08)},1
Style: Card,{font_name},{int(font_size * 1.55)},{white},{white},&H70000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,5,{margin},{margin},{int(height * 0.08)},1
Style: Title,{font_name},{int(font_size * 0.6)},{_bgr(accent)},{_bgr(accent)},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,{margin},{margin},{int(height * 0.05)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if title.strip():
        if intro > 0:
            lines.append(f"Dialogue: 0,{_fmt_ass(0.15)},{_fmt_ass(intro)},Card,,0,0,0,,{{\\fad(600,500)\\blur1}}{esc(title.strip())}\n")
        elif duration > 0:
            lines.append(f"Dialogue: 0,{_fmt_ass(0)},{_fmt_ass(duration)},Title,,0,0,0,,{{\\fad(600,600)}}{esc(title.strip())}\n")
    for a, b, t in cues:
        body = _karaoke(esc(t), b - a) if karaoke else esc(t)
        lines.append(f"Dialogue: 1,{_fmt_ass(a)},{_fmt_ass(b)},Default,,0,0,0,,{{\\fad(160,0)\\blur0.8}}{body}\n")
    return head + "".join(lines)
