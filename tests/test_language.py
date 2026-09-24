"""Language / genre mapping checks (no GPU): python tests/test_language.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import flow  # noqa: E402

ZH = "[Verse]\n清晨的光落在窗台\n咖啡的香慢慢散开"
JA = "[Verse]\n朝の光が窓に落ちて\nコーヒーの香りが広がる"
KO = "[Verse]\n아침 햇살이 창가에 내려\n커피 향기가 퍼져가"
EN = "[Verse]\nMorning light upon the sill\nCoffee warm and time stands still"
checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    assert cond, msg


for text, lang in ((ZH, "zh"), (JA, "ja"), (KO, "ko"), (EN, "en"), ("[Verse]\n", None), (None, None)):
    ok(flow.detect_language(text) == lang, f"detect {lang}: {flow.detect_language(text)}")
# Japanese written mostly in kanji still has kana
ok(flow.detect_language("[Verse]\n東京の夜空に星が光る") == "ja", "kanji-heavy Japanese")


def spec(answers, agent=False):
    s = flow.new_state(agent)
    for v in answers:
        s = flow.answer(s, v)
    q = flow.question(s)
    ok(q["done"], f"wizard not done at {q.get('step')}")
    return q["spec"]


# web: text_song → lyrics, genre, mood, vocal, language, tempo, plan, variants (memory is a global switch now)
base = ["text", "text_song"]
tail = ["128", "full", "1"]
s = spec(base + [ZH, "pop", "warm", "f_bright", "auto"] + tail)
ok(s["style"].startswith("Mandarin") and not s["language_mismatch"], s["style"])
s = spec(base + [JA, "pop", "warm", "f_bright", "auto"] + tail)
ok(s["style"].startswith("Japanese") and s["language"] == "ja", s["style"])
s = spec(base + [ZH, "pop", "warm", "f_bright", "ja"] + tail)  # the reported bug
ok(s["language_mismatch"] == {"chosen": "ja", "lyrics": "zh"}, s["language_mismatch"])
s = spec(base + [ZH, "pop", "warm", "f_bright", "yue"] + tail)  # Cantonese is written in Han characters
ok(s["style"].startswith("Cantonese") and not s["language_mismatch"], s)
s = spec(base + [EN, "pop", "warm", "f_bright", "en"] + tail)
ok(s["style"].startswith("English") and not s["language_mismatch"], s)

# agent writes lyrics → "auto" is not offered, language is explicit
st = flow.new_state(True)
for v in ["text", "text_song", "agent", "主题"]:
    st = flow.answer(st, v)
while (q := flow.question(st))["step"] != "language":
    st = flow.answer(st, q["all_options"][0]["value"] if q["type"] == "choice" else "x")
ok("auto" not in [o["value"] for o in q["all_options"]], "auto offered to an agent that writes lyrics")

# lead instrument strips the genre's default instruments
s = spec(["text", "instrumental", "ballad", "guzheng", "warm", "88", "short", "1"])
ok("piano" not in s["style"] and "guzheng" in s["style"], s["style"])
s = spec(["text", "instrumental", "rock", "piano", "warm", "88", "short", "1"])
ok("electric guitars" not in s["style"] and "piano" in s["style"], s["style"])
s = spec(base + [ZH, "rock", "warm", "f_bright", "auto"] + tail)  # songs keep the genre's instruments
ok("electric guitars" in s["style"], s["style"])

# lyrics supplied later (hum / cover / refine) get the matching tag, or are refused
ok(flow.fit_language("modern pop, 108 BPM", ZH) == "Mandarin, modern pop, 108 BPM", "fit zh")
ok(flow.fit_language("Japanese, modern pop", JA) == "Japanese, modern pop", "fit keep ja")
try:
    flow.fit_language("Japanese, modern pop", ZH)
    ok(False, "mismatch not refused")
except ValueError as exc:
    ok("日语" in str(exc), str(exc))
print(f"OK ({checks} checks)")
