"""Runs one job spec: transcribe (SheetSage2) → edit ABC → generate (YuE2).

Each model runs in its own subprocess, so the GPU is fully released between stages.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import abcutil, config, flow
from .flow import FLOW

MIN_HUM_SECONDS = 20  # 哼唱 → 纯音乐: shorter melodies get sung (docs/EXPERIMENTS.md)


class NeedsLyrics(Exception):
    pass


class Cancelled(Exception):
    pass


def _run(cmd, log, job, env=None):
    log.write(f"\n$ {' '.join(map(str, cmd))}\n")
    log.flush()
    exe = str(cmd[0])
    if not (Path(exe).is_file() or shutil.which(exe)):
        raise RuntimeError(f"找不到程序 {exe}，请先运行 install.bat 完成安装（见 README）")
    base_env = {"HF_HOME": str(config.HF_HOME), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen(list(map(str, cmd)), stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, **base_env, **(env or {})}, cwd=config.ROOT,
                            creationflags=config.NO_WINDOW)
    job.proc = proc
    code = proc.wait()
    job.proc = None
    if job.cancelled:
        raise Cancelled()
    if code:
        raise RuntimeError(f"{Path(str(cmd[0])).name} exited with {code}; see log")


def _profile(name):
    if name == "auto":
        name = config.auto_profile()
    return name, FLOW["vram_profiles"][name]


def _base(job_id):
    base_dir = config.DATA / "jobs" / job_id
    meta = json.loads((base_dir / "job.json").read_text(encoding="utf-8"))
    takes = meta.get("takes") or []
    score = next((base_dir / t["score"] for t in takes if t.get("score")), None)
    if score is None or not score.exists():
        raise ValueError(f"Job {job_id} has no score to edit (cot=off jobs cannot be refined)")
    return meta, score.read_text(encoding="utf-8")


def sync_remote_code(model_dir):
    """Transformers copies only statically imported remote-code files; SheetSage2 also imports some lazily."""
    cache = config.HF_HOME / "modules" / "transformers_modules" / model_dir.name
    if model_dir.exists():
        cache.mkdir(parents=True, exist_ok=True)
        for src in model_dir.glob("*.py"):
            dst = cache / src.name
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst)


def transcribe(job, spec, out, log):
    src = config.DATA / spec["audio"]
    wav = out / "input.wav"
    # 2 s of trailing silence: a note cut off at the very end cannot be placed on the beat grid.
    _run([config.FFMPEG, "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "44100",
          "-af", "apad=pad_dur=2", wav], log, job)
    tdir = out / "transcription"
    job.set(stage="扒谱中 (SheetSage2)")
    ss2 = config.MODELS / "SheetSage2"
    sync_remote_code(ss2)
    mert = config.MODELS / "MERT-v2-FullSong"
    local = ss2.exists() and mert.exists()
    _run([config.SS2_PYTHON, config.SKILL_SCRIPTS / "transcribe.py", wav, "--task", spec["transcribe"],
          "--output", tdir, "--model", ss2 if ss2.exists() else "m-a-p/SheetSage2"]
         + (["--base-model", mert] if mert.exists() else []), log, job,
         # Both models are local (ModelScope copies, byte-identical to the pinned Hugging Face commits): never go online.
         env={"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"} if local else None)
    score = tdir / "score.abc"
    keep = spec.get("keep_voice")
    target = spec.get("target_voice")
    if target:
        # A hum may be heard as voice or as an instrument; take whichever part has the melody.
        abc = score.read_text(encoding="utf-8")
        other = "Ins" if target == "Vocal" else "Vocal"
        if abcutil.voice_notes(abc, other) > abcutil.voice_notes(abc, target):
            abc = abcutil.swap_voices(abc)
        score = out / "melody.abc"
        score.write_text(abc, encoding="utf-8")
        keep = target
    if keep:
        stripped = out / "stripped.abc"
        stripped.unlink(missing_ok=True)
        _run([config.TOOLS_PYTHON, config.SKILL_SCRIPTS / "abc_tools.py", "strip-chords", score, stripped,
              "--keep-voice", keep], log, job)
        score = stripped
    abc = score.read_text(encoding="utf-8")
    if target and not abcutil.voice_notes(abc, target):
        raise RuntimeError("没能从录音里识别出旋律：哼得再清楚些、节拍稳一些，或者录 20 秒以上再试")
    return abc


def _generate(job, out, rows, profile, log):
    """Run studio.runner for all takes; returns (takes, error). Nonzero exit only when every take failed."""
    cmd = [config.YUE2_PYTHON, "-m", "studio.runner", "--job", out,
           "--budget", profile["budget"], "--quantization", profile["quantization"]]
    if profile["offload_ar"]:
        cmd.append("--offload-ar")
    error = None
    try:
        _run(cmd, log, job)
    except RuntimeError as exc:
        error = exc
    takes = []
    for row in rows:
        d = out / "takes" / row["id"]
        meta = json.loads((d / "studio.json").read_text(encoding="utf-8")) if (d / "studio.json").exists() else {}
        takes.append({"name": row["id"], "seed": row["seed"],
                      "audio": f"takes/{row['id']}/audio.flac" if (d / "audio.flac").exists() else None,
                      "score": f"takes/{row['id']}/score.abc" if (d / "score.abc").exists() else None,
                      "audio_seconds": meta.get("audio_seconds"),
                      "generation_seconds": meta.get("generation_seconds"),
                      "post": meta.get("post"),
                      "truncated": (meta.get("truncated") or {}).get("semantic"),
                      "failure": json.loads((d / "failure.json").read_text()) if (d / "failure.json").exists() else None})
    job.set(takes=takes)
    return takes, error


def run(job):
    spec, out = job.spec, job.dir
    log = open(out / "log.txt", "a", encoding="utf-8")
    try:
        profile_name, profile = _profile(spec.get("vram", "auto"))
        style, lyrics, cot = spec.get("style"), spec.get("lyrics"), spec.get("cot", "full")
        score_file = out / "score.abc"
        if spec.get("base_job"):
            base, base_abc = _base(spec["base_job"])
            style = style or base.get("final_style") or base["spec"]["style"]
            lyrics = lyrics or base.get("final_lyrics") or base["spec"]["lyrics"]
            if base["spec"].get("instrumental"):  # a refined instrumental must stay instrumental
                spec = {**spec, "instrumental": True}
        if score_file.exists():
            abc = score_file.read_text(encoding="utf-8")  # resumed after lyrics or a restart
        elif spec.get("base_job"):
            abc = spec.get("abc") or base_abc
        elif spec.get("audio"):
            job.set(stage="转换音频")
            abc = transcribe(job, spec, out, log)
            if spec.get("instrumental") and abcutil.duration_seconds(abc) < MIN_HUM_SECONDS:
                # Measured: ~10 s hums were sung instead of played in 7 of 9 takes, ~34 s hums in 0 of 3.
                raise RuntimeError(f"扒出的旋律只有 {abcutil.duration_seconds(abc):.0f} 秒。纯音乐版需要至少 "
                                   f"{MIN_HUM_SECONDS} 秒的旋律，太短时模型会自己把旋律唱出来。请哼长一些再试")
        else:
            abc = None
        if abc is not None:
            if spec.get("bpm"):
                abc = abcutil.set_tempo(abc, spec["bpm"])
            score_file.write_text(abc, encoding="utf-8")
            (out / "score_check.json").unlink(missing_ok=True)  # abc_tools refuses to overwrite reports
            _run([config.TOOLS_PYTHON, config.SKILL_SCRIPTS / "abc_tools.py", "inspect", score_file,
                  "--output", out / "score_check.json"], log, job)
            (out / "phrases.json").write_text(json.dumps(abcutil.phrase_report(abc), ensure_ascii=False, indent=1),
                                              encoding="utf-8")
        if not lyrics:
            raise NeedsLyrics()
        if not style:
            raise ValueError("style is empty")
        if not spec.get("instrumental"):
            # Last line of defence: the language tag must describe the lyrics that will be sung
            # (e.g. a refined song keeps its lyrics while the style is rebuilt without a language).
            style = flow.fit_language(style, lyrics)
        if cot == "off":
            abc = None
        rows = [{"id": f"take-{i + 1}", "style": style, "lyrics": lyrics, "cot": cot,
                 "seed": spec["seed"] + i, **({"abc": abc} if abc else {})}
                for i in range(spec.get("variants", 1))]
        batch = out / "batch.jsonl"
        shutil.rmtree(out / "takes", ignore_errors=True)  # a retry must start clean
        batch.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        # Controls applied to each take's plan between planning and audio (see studio/runner.py).
        post = {"bpm": spec.get("bpm"), "target_seconds": spec.get("target_seconds"),
                "instrumental": bool(spec.get("instrumental")), "vocal_register": spec.get("vocal_register")}
        if spec.get("audio") and abc and not post["target_seconds"]:
            # Hum / reference: the result should be as long as the source; cap runaway continuations.
            post["target_seconds"] = round(abcutil.duration_seconds(abc) * 1.15, 1)
        (out / "post.json").write_text(json.dumps(post), encoding="utf-8")
        job.set(final_style=style, final_lyrics=lyrics)
        while True:
            job.set(stage=f"生成中 ({len(rows)} 个版本, 显存档位 {profile_name})")
            takes, error = _generate(job, out, rows, profile, log)
            out_of_memory = any("out of memory" in ((t["failure"] or {}).get("reason") or "").lower() for t in takes)
            if not (out_of_memory and profile.get("fallback")):
                break
            # The fast profile keeps the whole model on the GPU; if another program took memory, retry offloaded.
            log.write(f"\n[studio] out of GPU memory with {profile_name}; retrying with {profile['fallback']}\n")
            profile_name = profile["fallback"]
            profile = FLOW["vram_profiles"][profile_name]
            shutil.rmtree(out / "takes", ignore_errors=True)
        if not any(t["audio"] for t in takes):
            raise error or RuntimeError("No take produced audio; see log")
    finally:
        log.close()
