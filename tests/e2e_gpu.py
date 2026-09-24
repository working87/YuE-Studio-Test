"""End-to-end GPU test: every feature once, through the same wizard the agents use. Needs the app running.

    .venv\\Scripts\\python.exe tests\\e2e_gpu.py            (app on the default port 7860; set STUDIO_PORT otherwise)

Uses only material in this repo (samples/test_melody.wav and lyrics written here). The generated written song
doubles as the "reference song" for the cover features, so no third-party music is involved.
Takes about 10 minutes on a 16 GB card.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import agent, config  # noqa: E402

LYRICS = "[Verse]\n晚风吹过旧街角\n路灯把影子拉长\n\n[Chorus]\n我们唱着那首歌\n一直唱到天亮"
NEW_LYRICS = "[Verse]\n清晨的光落在窗台\n咖啡的香慢慢散开\n\n[Chorus]\n今天也要好好地爱\n把烦恼关在门外"
results = []


def run(name, answers, lyrics=None):
    s = agent.Session()
    s.call("wizard_start", {})
    r = s.call("wizard_fill", {"answers": {**answers, "variants": "1"}})
    nxt = r.get("next") or {}
    if r.get("errors") or not nxt.get("done"):
        results.append((name, "WIZARD", f"errors={r.get('errors')} next={nxt.get('step')}"))
        return None
    job = s.call("submit_song", {"title": f"e2e {name}", **({"lyrics": lyrics} if lyrics else {})})
    job_id = job["id"]
    t0 = time.time()
    while (j := agent.http("GET", f"/api/jobs/{job_id}"))["status"] in ("queued", "running"):
        time.sleep(5)
    takes = j.get("takes") or []
    ok = j["status"] == "done" and takes and takes[0].get("audio")
    detail = (f"{takes[0].get('audio_seconds')}s audio, generated in {takes[0].get('generation_seconds')}s"
              if ok else f"{j['status']}: {j.get('error')} {(j.get('log_tail') or [])[-5:]}")
    results.append((name, "OK" if ok else "FAIL", f"{detail} (total {time.time() - t0:.0f}s)"))
    print(f"{name}: {results[-1][1]} {detail}", flush=True)
    return j if ok else None


melody = agent.upload(ROOT / "samples/test_melody.wav")
song = run("写词作曲", {"feature": "text_song", "lyrics_source": "self", "lyrics": LYRICS,
                    "genre": "ballad", "mood": "warm", "vocal": "f_bright"})
run("纯音乐", {"feature": "instrumental", "genre": "lofi", "lead": "piano", "mood": "warm", "structure": "short"})
run("哼唱 → 带词歌曲", {"feature": "hum_song", "hum_audio": melody, "genre": "pop", "mood": "warm",
                      "hum_singer": "f_bright", "lyrics_source": "self", "lyrics": LYRICS})
run("哼唱 → 纯音乐", {"feature": "hum_instrumental", "hum_audio": melody, "genre": "lofi", "lead": "piano", "mood": "warm"})
if song:
    ref = str(config.DATA / "jobs" / song["id"] / song["takes"][0]["audio"])
    run("改编：换词、保持曲风", {"feature": "cover", "ref_audio": ref, "style_mode": "keep",
                        "orig_genre": "ballad", "vocal": "f_bright",
                        "lyrics_source": "self", "lyrics": NEW_LYRICS})
    run("改编：原词、换曲风", {"feature": "cover", "ref_audio": ref, "lyrics_source": "self", "lyrics": LYRICS,
                        "style_mode": "new", "harmony": "reharm", "genre": "jazz",
                         "mood": "warm", "vocal": "m_warm"})
    run("改谱精修（改速度）", {"feature": "remix", "base_job": song["id"], "edit_type": "tempo", "new_tempo": "100"})
print()
for name, status, detail in results:
    print(f"{status:6} {name}  {detail}")
failed = [r for r in results if r[1] != "OK"]
print("ALL PASS" if not failed and len(results) == 7 else f"FAILED {len(failed)} / {len(results)}")
sys.exit(1 if failed or len(results) != 7 else 0)
