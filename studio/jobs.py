"""File-backed job store with one GPU worker (YuE2 must not run concurrently on one GPU)."""
from __future__ import annotations

import json
import queue
import re
import threading
import time
import traceback
import uuid

from . import config, flow, pipeline

STATUSES = ("queued", "running", "needs_lyrics", "done", "failed", "cancelled")

# yue2 progress lines: "[YuE2] Running Synthesizing audio: 12/32 steps (38%) | elapsed 40.0s"
PROGRESS_LINE = re.compile(r"^\[YuE2\] (\w+) ([A-Za-z ]+?): (.*)$")
AMOUNT = re.compile(r"(\d+)/(\d+) \w+")
TOKENS = re.compile(r"(\d+) tokens \| ([\d.]+) tokens/s")
SONG = re.compile(r"^Song (\d+)/(\d+):")
PHASES = [("Planning score", "规划乐谱"), ("Generating song", "生成歌曲"),
          ("Synthesizing audio", "合成音频"), ("Decoding audio", "解码音频")]
PREP = {"Resolving model files": "准备模型", "Verifying model files": "校验模型", "Loading model": "加载模型",
        "Using provided score": "使用乐谱", "Loading audio decoder": "加载解码器"}


def progress(lines, data):
    """Current phase, step N of M and percent, parsed from the run log (for the progress bar)."""
    steps = (["扒谱"] if data["spec"].get("audio") and data["spec"].get("transcribe") else []) + [p[1] for p in PHASES]
    info = {"phase": data.get("stage") or "准备中", "step": 0, "steps": len(steps), "labels": steps,
            "percent": None, "detail": ""}
    if data.get("stage", "").startswith("扒谱"):
        info.update(phase="扒谱（SheetSage2）", step=1)
    take = next((f"版本 {m.group(1)}/{m.group(2)}" for line in reversed(lines) if (m := SONG.match(line))), None)
    for line in reversed(lines):
        m = PROGRESS_LINE.match(line)
        if not m:
            continue
        status, label, rest = m.groups()
        names = dict(PHASES)
        if label in names:
            info["phase"] = names[label]
            info["step"] = steps.index(names[label]) + 1
            if status == "Completed":
                info["percent"] = 100
            elif (a := AMOUNT.search(rest)) and int(a.group(2)):
                info["percent"] = round(100 * int(a.group(1)) / int(a.group(2)))
            if (t := TOKENS.search(rest)):
                info["detail"] = f"{t.group(1)} tokens · {t.group(2)} tokens/s"
            elif info["percent"] is not None:
                info["detail"] = rest.split(" | ")[0]
        elif label in PREP:
            info["phase"], info["detail"] = PREP[label], rest.split(" | ")[-1]
        if info["percent"] is not None or info["detail"]:
            break
    if take and info["steps"]:
        info["take"] = take
    return info


class Job:
    def __init__(self, data):
        self.data = data
        self.proc = None
        self.cancelled = False
        self.lock = threading.Lock()

    @property
    def id(self):
        return self.data["id"]

    @property
    def dir(self):
        return config.DATA / "jobs" / self.id

    @property
    def spec(self):
        return self.data["spec"]

    def set(self, **fields):
        with self.lock:
            self.data.update(fields, updated=time.time())
            self.dir.mkdir(parents=True, exist_ok=True)
            tmp = self.dir / "job.json.tmp"
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.dir / "job.json")

    def view(self, log_lines=40):
        data = dict(self.data)
        log = self.dir / "log.txt"
        if log.exists():
            text = log.read_text(encoding="utf-8", errors="replace").replace("\r", "\n")
            lines = [l for l in text.splitlines() if l.strip()]
            data["log_tail"] = lines[-log_lines:]
            if data["status"] == "running":
                data["progress"] = progress(lines, data)
        for name in ("phrases.json", "score_check.json"):
            f = self.dir / name
            if f.exists():
                data[name.split(".")[0]] = json.loads(f.read_text(encoding="utf-8"))
        if (self.dir / "score.abc").exists():
            data["score"] = (self.dir / "score.abc").read_text(encoding="utf-8")
        return data


class Store:
    def __init__(self):
        (config.DATA / "jobs").mkdir(parents=True, exist_ok=True)
        (config.DATA / "uploads").mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, Job] = {}
        self.queue: queue.Queue[str] = queue.Queue()
        for f in sorted((config.DATA / "jobs").glob("*/job.json")):
            job = Job(json.loads(f.read_text(encoding="utf-8")))
            self.jobs[job.id] = job
            if job.data["status"] in ("queued", "running"):
                job.set(status="queued", stage="服务重启后重新排队")
                self.queue.put(job.id)
        threading.Thread(target=self._worker, daemon=True).start()

    def create(self, spec, title=None):
        job_id = time.strftime("%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
        job = Job({"id": job_id, "title": title or spec.get("label", "song"), "created": time.time(),
                   "status": "queued", "stage": "排队中", "spec": spec, "takes": []})
        job.set()
        self.jobs[job_id] = job
        self.queue.put(job_id)
        return job

    def supply_lyrics(self, job_id, lyrics, style=None):
        job = self.jobs[job_id]
        if job.data["status"] not in ("needs_lyrics", "failed"):
            raise ValueError(f"Job is {job.data['status']}, not waiting for lyrics")
        spec = {**job.spec, "lyrics": flow.normalize_lyrics(lyrics), **({"style": style} if style else {})}
        if not spec.get("instrumental"):
            spec["style"] = flow.fit_language(spec.get("style"), lyrics)  # ValueError on a language mismatch
        job.set(spec=spec, status="queued", stage="排队中", error=None)
        self.queue.put(job_id)
        return job

    def cancel(self, job_id):
        job = self.jobs[job_id]
        job.cancelled = True
        if job.proc:
            job.proc.terminate()
        if job.data["status"] in ("queued", "needs_lyrics"):
            job.set(status="cancelled", stage="已取消")
        return job

    def list(self):
        return sorted((j.data for j in self.jobs.values()), key=lambda d: d["created"], reverse=True)

    def _worker(self):
        while True:
            job = self.jobs[self.queue.get()]
            if job.cancelled or job.data["status"] == "cancelled":
                continue
            job.set(status="running", stage="准备中", started=time.time())
            try:
                pipeline.run(job)
                job.set(status="done", stage="完成", finished=time.time())
            except pipeline.NeedsLyrics:
                job.set(status="needs_lyrics", stage="等待歌词：旋律已扒好，请按下表的句数和字数填词")
            except pipeline.Cancelled:
                job.set(status="cancelled", stage="已取消")
            except Exception as exc:
                with open(job.dir / "log.txt", "a", encoding="utf-8") as log:
                    log.write(traceback.format_exc())
                job.set(status="failed", stage="失败", error=f"{type(exc).__name__}: {exc}")
