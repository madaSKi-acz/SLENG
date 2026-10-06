"""Text preparation for Khmer TTS: normalize, spell out numbers, split into chunks."""
import re

KH_DIGITS = "០១២៣៤៥៦៧៨៩"
_DIGIT_WORDS = ["សូន្យ", "មួយ", "ពីរ", "បី", "បួន", "ប្រាំ", "ប្រាំមួយ", "ប្រាំពីរ", "ប្រាំបី", "ប្រាំបួន"]
_TENS = {2: "ម្ភៃ", 3: "សាមសិប", 4: "សែសិប", 5: "ហាសិប", 6: "ហុកសិប", 7: "ចិតសិប", 8: "ប៉ែតសិប", 9: "កៅសិប"}
# (value, word) from largest to smallest
_UNITS = [(10**6, "លាន"), (10**5, "សែន"), (10**4, "ម៉ឺន"), (10**3, "ពាន់"), (100, "រយ")]


def number_to_khmer(n: int) -> str:
    if n < 10:
        return _DIGIT_WORDS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        head = "ដប់" if tens == 1 else _TENS[tens]
        return head + (_DIGIT_WORDS[ones] if ones else "")
    for value, word in _UNITS:
        if n >= value:
            q, r = divmod(n, value)
            return number_to_khmer(q) + word + (number_to_khmer(r) if r else "")
    raise ValueError(n)


def _pad(words: str, text: str, start: int, end: int) -> str:
    """Add a space only where the neighbour is not Khmer (Khmer words are written unspaced)."""
    khmer = lambda ch: "\u1780" <= ch <= "\u17ff"
    left = " " if start > 0 and not khmer(text[start - 1]) and not text[start - 1].isspace() else ""
    right = " " if end < len(text) and not khmer(text[end]) and not text[end].isspace() else ""
    return left + words + right


def spell_numbers(text: str) -> str:
    """Replace Khmer/ASCII digit runs (with optional , or . separators) by Khmer words."""
    table = {ord(c): str(i) for i, c in enumerate(KH_DIGITS)}
    text = text.translate(table)

    def repl(m):
        raw = m.group(0)
        if "." in raw and not re.fullmatch(r"\d+\.\d+", raw):
            raw = raw.replace(".", "")
        if re.fullmatch(r"\d+\.\d+", raw):  # decimal: 3.5 -> បី ក្បៀស ប្រាំ
            a, b = raw.split(".")
            words = f"{number_to_khmer(int(a))}ក្បៀស{''.join(_DIGIT_WORDS[int(d)] for d in b)}"
            return _pad(words, m.string, m.start(), m.end())
        n = int(raw.replace(",", ""))
        return _pad(number_to_khmer(n), m.string, m.start(), m.end())

    return re.sub(r"\d[\d,]*(?:\.\d+)?", repl, text)


def normalize(text: str) -> str:
    text = spell_numbers(text)
    text = text.replace("​", "")  # zero-width space
    text = re.sub(r"[()\[\]{}\"“”«»]", " ", text)
    text = re.sub(r"[,;:]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_chunks_ex(text: str, max_chars: int = 110):
    """Split text into chunks. Returns dicts: display (original text, for subtitles),
    speak (normalized, digits spelled out, for the TTS engine) and kind
    ('phrase' = mid-sentence cut, 'sentence', 'paragraph').

    Splits on paragraph breaks and the Khmer full stop (។ ៕ ? !), then breaks
    over-long sentences at spaces (Khmer uses spaces between phrases).
    The length limit is measured on the spoken text, where numbers are longer.
    """
    out = []
    for para in re.split(r"\n\s*\n|\n", text):
        para = re.sub(r"[ \t\u200b]+", " ", para).strip()
        if not para:
            continue
        sentences = [x.strip() for x in re.split(r"(?<=[។៕?!])", para) if x.strip()]
        pieces = []
        for sent in sentences:
            if len(normalize(sent)) <= max_chars:
                pieces.append(sent)
                continue
            cur = ""
            for phrase in sent.split(" "):
                if cur and len(normalize(f"{cur} {phrase}")) > max_chars:
                    pieces.append(cur)
                    cur = phrase
                else:
                    cur = f"{cur} {phrase}".strip()
            if cur:
                pieces.append(cur)
        pieces = [(d, normalize(d)) for d in pieces]
        pieces = [(d, sp) for d, sp in pieces if sp]
        for i, (d, sp) in enumerate(pieces):
            if i == len(pieces) - 1:
                kind = "paragraph"
            elif d[-1] in "។៕?!":
                kind = "sentence"
            else:
                kind = "phrase"
            out.append({"display": d, "speak": sp, "kind": kind})
    return out


def split_chunks(text: str, max_chars: int = 110):
    """Yield (spoken_text, pause_kind) pairs."""
    return [(c["speak"], c["kind"]) for c in split_chunks_ex(text, max_chars)]
