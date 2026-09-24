"""The 16g profile retries with 16g-safe when takes fail with CUDA OOM (simulated; no GPU needed)."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from studio import pipeline  # noqa: E402

calls = []


def fake_generate(job, out, rows, profile, log):
    calls.append(profile)
    if not profile["offload_ar"]:
        takes = [{"name": "take-1", "audio": None, "failure": {"reason": "CUDA out of memory. Tried to allocate 4.9 GiB"}}]
    else:
        takes = [{"name": "take-1", "audio": "takes/take-1/audio.flac", "failure": None}]
    job.set(takes=takes)
    return takes, None


class Job:
    def __init__(self, d):
        self.dir, self.spec, self.data = d, {"style": "Mandarin, pop", "lyrics": "[Verse]\n你好", "cot": "off",
                                           "variants": 1, "seed": 1, "vram": "16g"}, {}
        self.proc, self.cancelled = None, False

    def set(self, **kw):
        self.data.update(kw)


pipeline._generate = fake_generate
with tempfile.TemporaryDirectory() as tmp:
    job = Job(Path(tmp))
    pipeline.run(job)
assert [p["offload_ar"] for p in calls] == [False, True], calls
assert job.data["takes"][0]["audio"], job.data
assert "16g-safe" in job.data["stage"], job.data["stage"]
print("OOM fallback OK: 16g (fast) -> 16g-safe; stage:", job.data["stage"])
