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


def to_ass(cues, width, height, font_name, font_size):
    esc = lambda t: t.replace("\\", "").replace("{", "(").replace("}", ")")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,5,{int(width * 0.08)},{int(width * 0.08)},{int(height * 0.08)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + "".join(f"Dialogue: 0,{_fmt_ass(a)},{_fmt_ass(b)},Default,,0,0,0,,{esc(t)}\n" for a, b, t in cues)
