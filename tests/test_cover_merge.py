"""参考歌曲改编: one lyrics box (original words = sing them, new words = new lyrics, empty = fill after
transcription) plus style / harmony / singer; every combination asks the right things and picks the right pipeline.

    .venv\\Scripts\\python.exe tests\\test_cover_merge.py      (no GPU, no server)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import flow  # noqa: E402

LYRICS = "[Verse]\n晚风吹过旧街角\n路灯把影子拉长"
fails = 0


def check(name, ok, detail=""):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail and not ok else ""))


def asked(answers):
    """Steps an agent wizard still asks (in order) for a cover with these answers already given."""
    s = flow.new_state(agent=True)
    s, _, errors, _ = flow.fill(s, {"feature": "cover", "ref_audio": "uploads/x.mp3", **answers})
    assert not errors, errors
    order = []
    for _ in range(30):
        q = flow.question(s, page_size=None)
        if q.get("done"):
            return order, q["spec"]
        order.append(q["step"])
        opts = [o["value"] for o in q.get("options", [])]
        s = flow.answer(s, {"lyrics": LYRICS, "theme": "离别"}.get(q["step"], opts[0] if opts else "x"))
    raise AssertionError("wizard did not finish")


steps = flow.FLOW["features"]["cover"]["steps"]
check("old features gone, one cover feature", "cover" in flow.FLOW["features"]
      and not {"cover_lyrics", "cover_style"} & set(flow.FLOW["features"]))
check("no separate 'keep / new lyrics' question", "lyrics_mode" not in steps and "orig_lyrics" not in steps, str(steps))

# only change the style: the original words in the lyrics box, new style, new harmony
order, spec = asked({"lyrics_source": "self", "lyrics": LYRICS, "style_mode": "new", "harmony": "reharm",
                     "genre": "jazz", "mood": "warm", "vocal": "f_bright"})
check("restyle: nothing else asked", order == [], str(order))
check("restyle + new harmony → melody only", spec["transcribe"] == "melody-full" and spec["cot"] == "melody"
      and spec["target_voice"] == "Vocal", str(spec))
check("restyle: sings the given words", "晚风" in (spec["lyrics"] or ""))
check("restyle: new style in the description", "jazz" in spec["style"].lower(), spec["style"])
check("restyle: language read off the lyrics", spec["style"].startswith("Mandarin"), spec["style"])

_, spec = asked({"lyrics_source": "self", "lyrics": LYRICS, "style_mode": "new", "harmony": "keep",
                 "genre": "jazz", "mood": "warm", "vocal": "f_bright"})
check("restyle + keep harmony → chords kept", spec["transcribe"] == "full" and spec["cot"] == "full", str(spec))

# only change the singer: same words, original style
order, spec = asked({"lyrics_source": "self", "lyrics": LYRICS, "style_mode": "keep", "orig_genre": "ballad",
                     "vocal": "m_warm"})
check("new singer: nothing else asked", order == [], str(order))
check("new singer → chords kept", spec["transcribe"] == "full" and spec["cot"] == "full")
check("new singer: original style described", "ballad" in spec["style"].lower(), spec["style"])
check("new singer: new voice", "male" in spec["style"].lower(), spec["style"])

# the agent writes new lyrics after transcription (the old 换词 with AI)
order, spec = asked({"lyrics_source": "agent", "theme": "离别", "style_mode": "keep", "orig_genre": "ballad",
                     "vocal": "f_bright", "language": "zh"})
check("AI lyrics: nothing else asked", order == [], str(order))
check("AI lyrics: written after transcription", "write_lyrics_after_transcription" in spec["todo"], str(spec["todo"]))

# steps that must NOT be asked for the choices made
order, _ = asked({"lyrics_source": "self", "lyrics": LYRICS, "style_mode": "keep", "orig_genre": "pop",
                  "vocal": "f_bright"})
check("style kept: no genre / mood / harmony", not {"genre", "mood", "harmony"} & set(order), str(order))
order, _ = asked({"lyrics_source": "self", "lyrics": LYRICS, "style_mode": "new", "genre": "rock", "mood": "hype",
                  "vocal": "f_bright"})
check("style changed: harmony asked", "harmony" in order and "orig_genre" not in order, str(order))

# the web form: one lyrics box, and leaving it empty is allowed (fill in after transcription)
web_steps = flow.feature_steps({"category": "ref", "feature": "cover"})
web = {"category": "ref", "feature": "cover", "ref_audio": "uploads/x.mp3", "style_mode": "keep",
       "orig_genre": "ballad", "vocal": "f_bright", "language": "auto", "variants": "1"}
check("web: lyrics box shown", flow.visible("lyrics", web, web_steps, agent=False))
check("web: empty lyrics allowed", "lyrics" not in flow.pending({"answers": web, "agent": False}),
      str(flow.pending({"answers": web, "agent": False})))

# switching a choice in the form must not let the hidden answer leak into the song
leaky = {**web, "lyrics": LYRICS, "genre": "metal", "mood": "angry"}
spec = flow.build_spec({"answers": leaky, "agent": False})
check("hidden new style ignored", "metal" not in spec["style"].lower() and "angry" not in spec["style"].lower(),
      spec["style"])
leaky.update(style_mode="new", harmony="reharm", genre="metal", mood="angry")
spec = flow.build_spec({"answers": leaky, "agent": False})
check("hidden original style ignored", "ballad" not in spec["style"].lower(), spec["style"])
spec = flow.build_spec({"answers": {"category": "text", "feature": "text_song", "lyrics": "[Verse]\n网页里写的词",
                                    "genre": "pop", "mood": "warm", "vocal": "f_bright", "language": "auto",
                                    "tempo": "108", "plan_mode": "full", "variants": "1"}, "agent": False})
check("web text song keeps its typed lyrics", "网页里写的词" in (spec["lyrics"] or ""), str(spec["lyrics"]))

for feature in ("hum_song", "text_song"):
    st = flow.feature_steps({"category": "x", "feature": feature})
    check(f"{feature}: lyrics source still asked", flow.visible("lyrics_source", {"feature": feature}, st, agent=True))
print("FAILED" if fails else "ALL PASS", fails)
sys.exit(1 if fails else 0)
