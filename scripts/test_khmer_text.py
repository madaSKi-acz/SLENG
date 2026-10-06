from khmer_text import number_to_khmer, split_chunks, spell_numbers

assert number_to_khmer(65) == "ហុកសិបប្រាំ"
assert number_to_khmer(385) == "បីរយ" + "ប៉ែតសិបប្រាំ"
assert number_to_khmer(1600) == "មួយពាន់ប្រាំមួយរយ"
assert number_to_khmer(101_000_000) == "មួយរយមួយលាន"
assert number_to_khmer(10) == "ដប់" and number_to_khmer(0) == "សូន្យ"
assert "៦៥" not in spell_numbers("៦៥រូប") and "ហុកសិបប្រាំ" in spell_numbers("៦៥រូប")
sample = open(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "data", "sample_long.txt"), encoding="utf-8").read()
chunks = split_chunks(sample, 110)
assert chunks and all(len(c) <= 140 for c, _ in chunks), max(len(c) for c, _ in chunks)
assert not any(ch.isdigit() or ch in "០១២៣៤៥៦៧៨៩" for c, _ in chunks for ch in c)
for c, k in chunks:
    print(k[:4], len(c), c)
print("OK", len(chunks), "chunks")
