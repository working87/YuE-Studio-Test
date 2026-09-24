"""Agent path: open question → wizard_start → one wizard_fill → only the missing items → done with defaults.

    .venv\\Scripts\\python.exe tests\\test_agent_fill.py
(the audio checks that upload a local file need the app running on 127.0.0.1:7860)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import agent, config, flow  # noqa: E402

fails = 0


def check(name, ok, detail=""):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail and not ok else ""))


s = agent.Session()
start = s.call("wizard_start", {})
fields = {f["feature"]: f["fields"] for f in start["features"]}
check("start lists all 7 features", len(fields) == 7, str(list(fields)))
check("no technical fields exposed", not any(k in f for f in fields.values() for k in ("vram", "variants", "tempo", "plan_mode")),
      str(fields["text_song"]))

# "随便写首歌": the agent picks everything in one call
r = s.call("wizard_fill", {"answers": {"feature": "text_song", "lyrics_source": "agent", "theme": "夏天的海边",
                                       "genre": "pop", "mood": "warm", "vocal": "f_bright", "language": "zh",
                                       "structure": "standard"}})
check("one fill completes a text song", r["next"].get("done") is True, str(r)[:300])
check("category inferred from feature", s.state["answers"].get("category") == "text")
check("defaults reported", r["next"].get("defaults", {}).get("variants") == "1 个版本", str(r["next"].get("defaults")))
check("spec uses auto vram", r["next"]["spec"]["vram"] == "auto")

# the user's own lyrics: the language is read off them, not asked
s = agent.Session()
s.call("wizard_start", {})
r = s.call("wizard_fill", {"answers": {"feature": "text_song", "lyrics_source": "self", "genre": "pop", "mood": "warm",
                                       "vocal": "f_bright", "lyrics": "[Verse]\n晚风吹过旧街角\n路灯把影子拉长"}})
check("own lyrics: language not asked", r["next"].get("done") is True, str(r["next"].get("step")))
check("own lyrics: detected as Mandarin", r["next"].get("spec", {}).get("style", "").startswith("Mandarin"),
      str(r["next"].get("spec", {}).get("style"))[:60])
check("own lyrics: default listed", "language" in r["next"].get("defaults", {}), str(r["next"].get("defaults")))

# partial fill: only the missing item comes back, with every option at once
s = agent.Session()
s.call("wizard_start", {})
r = s.call("wizard_fill", {"answers": {"feature": "text_song", "lyrics_source": "agent", "theme": "失恋",
                                       "mood": "sad", "language": "yue", "nonsense": "x"}})
nxt = r["next"]
check("asks the first missing item", nxt.get("step") == "genre", str(nxt.get("step")))
check("all 61 genres at once, no paging", len(nxt.get("options", [])) == 61
      and not any(o["value"] == "__more__" for o in nxt["options"]), str(len(nxt.get("options", []))))
check("pinned genres first", nxt["options"][0].get("value") in {o["value"] for o in flow.FLOW["steps"]["genre"]["options"] if o.get("pin")})
check("mood filled out of order", s.state["answers"].get("mood") == "sad")
check("unknown key reported as ignored", "nonsense" in r.get("ignored", {}), str(r))
r = s.call("wizard_fill", {"answers": {"genre": "粤语流行 Cantopop"}})  # a label is fine too
check("label accepted", s.state["answers"].get("genre") == "cantopop", str(s.state["answers"].get("genre")))
check("next after genre is vocal", r["next"].get("step") == "vocal", str(r["next"].get("step")))
r = s.call("wizard_fill", {"answers": {"vocal": "bogus-voice-xyz"}})
check("bad value -> error, still asks vocal", "vocal" in r.get("errors", {}) or s.state["answers"].get("vocal") == "bogus-voice-xyz",
      str(r)[:200])

# audio: a chat attachment name is rejected at once, with guidance
s = agent.Session()
s.call("wizard_start", {})
r = s.call("wizard_fill", {"answers": {"feature": "hum_song", "hum_audio": "网非.mp3"}})
check("attachment name rejected immediately", "hum_audio" in r.get("errors", {}) or "error" in r, str(r)[:200])
msg = str(r.get("errors", {}).get("hum_audio") or r.get("error"))
check("error explains what to do", "YuE Studio 窗口" in msg and "完整路径" in msg, msg)
check("still waiting for the audio", (r.get("next") or {}).get("step") == "hum_audio", str(r.get("next"))[:120])
up = next((p for p in (config.DATA / "uploads").glob("*") if p.is_file()), None)
if up:
    r = s.call("wizard_fill", {"answers": {"hum_audio": f"uploads/{up.name}"}})
    check("existing upload accepted", s.state["answers"].get("hum_audio") == f"uploads/{up.name}", str(r)[:200])
try:
    agent.http("GET", "/api/system", timeout=5)
    running = True
except agent.ApiError as exc:
    running = False
    print("SKIP upload checks (app not running):", exc)
if running:
    local = ROOT / "samples/test_melody.wav"
    s2 = agent.Session()
    s2.call("wizard_start", {})
    r = s2.call("wizard_fill", {"answers": {"feature": "hum_instrumental", "hum_audio": str(local)}})
    check("local absolute path uploaded now", str(s2.state["answers"].get("hum_audio", "")).startswith("uploads/"), str(r)[:200])
    r = s2.call("wizard_fill", {"answers": {"genre": "lofi", "lead": "piano", "mood": "warm"}})
    check("hum_instrumental done, 4 versions by default", r["next"].get("done") and r["next"]["spec"]["variants"] == 4,
          str(r["next"])[:300])

# the one memory switch
gpu16, gpu24 = {"memory_gib": 15.9, "compute_cap": "12.0"}, {"memory_gib": 24, "compute_cap": "8.6"}
check("16GB fast", config.auto_profile(gpu16, "fast") == "16g")
check("16GB save", config.auto_profile(gpu16, "save") == "16g-safe")
check("24GB fast", config.auto_profile(gpu24, "fast") == "24g")
check("24GB save", config.auto_profile(gpu24, "save") == "16g-safe")
check("12GB RTX 40 → FP8", config.auto_profile({"memory_gib": 12, "compute_cap": "8.9"}, "fast") == "12g")
check("12GB RTX 30 → no FP8", config.auto_profile({"memory_gib": 12, "compute_cap": "8.6"}, "fast") == "12g-safe")
check("web form has no vram step", not any("vram" in f["steps"] for f in flow.FLOW["features"].values()))
print("FAILED" if fails else "ALL PASS", fails)
sys.exit(1 if fails else 0)
