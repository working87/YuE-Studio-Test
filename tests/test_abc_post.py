"""Check plan post-processing on a real YuE2 plan: python tests/test_abc_post.py [score.abc]  (default: a fixture)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor/YuE/skills/yue2-music/scripts")]
sys.stdout.reconfigure(encoding="utf-8")
from abc_tools import parse_abc  # official validator  # noqa: E402
from studio import abcutil as a  # noqa: E402


def info(abc, tag):
    parse_abc(abc)  # raises on invalid notation
    print(f"{tag:14} {a.duration_seconds(abc):6.1f}s  vocal notes {a.voice_notes(abc, 'Vocal'):4}  "
          f"ins notes {a.voice_notes(abc, 'Ins'):4}  valid")


src = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tests/fixtures/ballad_plan.abc").read_text(encoding="utf-8")
info(src, "original")
t60 = a.trim_to_seconds(src, 60)
info(t60, "trim 60s")
info(a.trim_to_seconds(src, 30), "trim 30s")
inst = a.instrumentalize(t60)
info(inst, "instrumental")
info(a.set_tempo(inst, 100), "tempo 100")
print("sections kept:", [l for l in inst.splitlines() if l.startswith("%")])
print("chord symbols:", inst.count('"'), "before:", t60.count('"'))
assert a.voice_notes(inst, "Vocal") == 0
assert a.duration_seconds(t60) <= 60 * 1.15
print("OK")
