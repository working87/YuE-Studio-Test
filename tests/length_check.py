"""Does the audio end where the score ends? (GPU, app running; set STUDIO_PORT if not 7860)

    .venv\\Scripts\\python.exe tests\\length_check.py

Instrumentals trimmed to a target length plus a hummed song, with fixed seeds. For each take prints the score
length, the audio length and whether it was cut off. With score-aligned generation the audio should be the score
plus about 2 s of decay, and nothing should be reported as truncated.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import agent, config  # noqa: E402

CASES = [
    # the case that used to be cut at 76 s: 60 s target, planned 122 s at 108 BPM
    ("国风电子 短 (原截断案例)", {"feature": "instrumental", "genre": "guofeng_edm", "lead": "guitar", "mood": "epic",
                            "tempo": "108", "structure": "short"}, 851426591),
    ("lofi 短", {"feature": "instrumental", "genre": "lofi", "lead": "piano", "mood": "warm", "structure": "short"}, 1234),
    ("爵士 短", {"feature": "instrumental", "genre": "jazz", "lead": "sax", "mood": "warm", "structure": "short"}, 5678),
    ("抒情 标准", {"feature": "instrumental", "genre": "ballad", "lead": "strings", "mood": "warm",
                "structure": "standard"}, 4242),
    ("哼唱 → 纯音乐", {"feature": "hum_instrumental", "genre": "lofi", "lead": "piano", "mood": "warm",
                    "variants": "1"}, 777),
]

melody = agent.upload(ROOT / "samples/test_melody.wav")
rows = []
for name, answers, seed in CASES:
    s = agent.Session()
    s.call("wizard_start", {})
    if answers["feature"] == "hum_instrumental":
        answers = {**answers, "hum_audio": melody}
    r = s.call("wizard_fill", {"answers": {**answers, "variants": answers.get("variants", "1")}})
    if not r["next"].get("done"):
        print(name, "wizard not done:", r)
        continue
    spec = {**r["next"]["spec"], "seed": seed}
    job_id = agent.http("POST", "/api/jobs", {"spec": spec, "title": f"长度检查 {name}"})["id"]
    rows.append((name, job_id))
    print("submitted", name, job_id, flush=True)

print()
for name, job_id in rows:
    while (job := agent.http("GET", f"/api/jobs/{job_id}"))["status"] in ("queued", "running"):
        time.sleep(5)
    for t in job.get("takes") or []:
        meta_path = config.DATA / "jobs" / job_id / "takes" / t["name"] / "studio.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        score, audio = meta.get("score_seconds"), meta.get("audio_seconds")
        over = f"{audio - score:+.1f}s" if score and audio else "?"
        print(f"{name:22} {job['status']:5} score {score}s  audio {audio}s  ({over})  "
              f"cut={bool((meta.get('truncated') or {}).get('semantic'))}  {' | '.join(meta.get('post') or [])}",
              flush=True)
