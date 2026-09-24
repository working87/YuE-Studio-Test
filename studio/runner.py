"""Generation runner, executed as a child process in .venv (it imports torch/yue2; the app server does not).

Replaces `yue2 batch` so the symbolic plan can be edited between planning and audio:
    plan → post-process ABC (tempo, target length, instrumental) → semantic → synthesis → VAE
One model load serves every take. Progress goes to stderr in yue2's own format, plus
"Song i/N: id" lines, which the studio parses for its progress bar.

    python -m studio.runner --job <job dir> --budget 16 --quantization none [--offload-ar]
Input:  <job>/batch.jsonl (one request per take), <job>/post.json (post-processing options)
Output: <job>/takes/<id>/  (yue2 native artifacts + score.abc) or failure.json
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor/YuE/skills/yue2-music/scripts"))

from studio import abcutil  # noqa: E402  (stdlib-only module)

TOKENS_PER_SECOND = 25  # YuE2 semantic codec rate (measured: 4110 tokens → 164.4 s)
MALE_MAX_WRITTEN_MEDIAN = 64  # MIDI (E4). Measured: female plans 76–77 → sung ~340 Hz; male plans 66–74 → sung
                              # 220–310 Hz; a male plan moved down to 61 → sung 139 Hz (clearly male).
FEMALE_MIN_WRITTEN_MEDIAN = 67  # MIDI (G4): a male-range score is raised for a female singer.


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def post_process(abc, post):
    """Apply the studio's controls to a plan; any failure falls back to the model's untouched plan
    (e.g. the planner occasionally writes a score without a K: line)."""
    try:
        return _post_process(abc, post)
    except Exception as exc:  # noqa: BLE001
        log(f"[studio] could not adjust the plan ({exc}); using the model's plan")
        return abc, ["乐谱无法调整（模型输出的乐谱不完整），按原乐谱生成：" + str(exc)[:80]]


def _post_process(abc, post):
    from abc_tools import parse_abc
    edited, notes = abc, []
    if post.get("bpm") and abcutil.tempo(edited) != post["bpm"]:  # before trimming: length depends on tempo
        edited = abcutil.set_tempo(edited, post["bpm"])
        notes.append(f"速度改为 {post['bpm']} BPM")
    if post.get("target_seconds"):
        before, untrimmed = abcutil.duration_seconds(edited), edited
        edited = abcutil.trim_to_seconds(edited, post["target_seconds"])
        if edited != untrimmed:
            notes.append(f"按时长裁剪 {before:.0f} 秒 → {abcutil.duration_seconds(edited):.0f} 秒")
    register = post.get("vocal_register")
    if register in ("male", "female"):
        # YuE2 often plans a male line as high as a female one (median A4–D5 written, sung ~D4), and a
        # refined male song keeps a male-range score. The written register decides the sung one.
        pitches = sorted(n[1] for n in parse_abc(edited).voices["Vocal"].notes)
        median = pitches[len(pitches) // 2] if pitches else None
        if median is not None and register == "male" and median > MALE_MAX_WRITTEN_MEDIAN:
            edited = abcutil.transpose_voice(edited, "Vocal", -1)
            notes.append("男声旋律降一个八度")
        elif median is not None and register == "female" and median < FEMALE_MIN_WRITTEN_MEDIAN:
            edited = abcutil.transpose_voice(edited, "Vocal", +1)
            notes.append("女声旋律升一个八度")
    if post.get("instrumental") and abcutil.voice_notes(edited, "Vocal"):
        edited = abcutil.instrumentalize(edited)
        notes.append("人声旋律改由乐器演奏")
    try:
        parse_abc(edited)
    except Exception as exc:  # noqa: BLE001
        log(f"[studio] post-processing produced invalid ABC ({exc}); using the model's plan")
        return abc, ["乐谱调整失败，已使用原乐谱：" + str(exc)[:120]]
    return edited, notes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--job", required=True, type=Path)
    p.add_argument("--budget", type=float, default=24)
    p.add_argument("--quantization", default="none")
    p.add_argument("--offload-ar", action="store_true")
    args = p.parse_args()

    import numpy as np
    from yue2.pipeline import SongResult, YuE2Pipeline
    from yue2.storage import identity, write_json

    rows = [json.loads(l) for l in (args.job / "batch.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    post = json.loads((args.job / "post.json").read_text(encoding="utf-8")) if (args.job / "post.json").exists() else {}
    models = ROOT / "models"
    pipe = YuE2Pipeline.from_pretrained(str(models / "YuE2-3B"), vae=str(models / "YuE2-Vae"), device="cuda",
                                        memory_budget_gib=args.budget, quantization=args.quantization,
                                        offload_ar=args.offload_ar, local_files_only=True,
                                        vae_core_frames=512 if args.budget <= 12 else 1024)
    failures = 0
    try:
        for index, row in enumerate(rows, 1):
            log(f"Song {index}/{len(rows)}: {row['id']}")
            out = args.job / "takes" / row["id"]
            out.mkdir(parents=True, exist_ok=True)
            started = time.perf_counter()
            try:
                request = pipe._request(style=row["style"], lyrics=row["lyrics"], cot=row["cot"],
                                        seed=row["seed"], abc=row.get("abc"), id=row["id"])
                plan = pipe.plan(request=request)
                notes = []
                if plan.abc is not None and post:
                    edited, notes = post_process(plan.abc, post)
                    if edited != plan.abc:
                        (out / "plan_original.abc").write_text(plan.abc, encoding="utf-8")
                        request = dataclasses.replace(request, abc=edited)
                        plan = pipe.plan(request=request)
                sampling = None
                if post.get("target_seconds"):  # hard stop in case the model keeps playing past the plan
                    sampling = {"max_tokens": int(post["target_seconds"] * 1.2 * TOKENS_PER_SECOND) + 100}
                semantic = pipe.generate_semantic(plan, sampling=sampling)
                latents = pipe.synthesize(semantic)
                audio = pipe.decode(latents)
                if semantic.truncated:  # cut at the length cap: fade out instead of stopping dead
                    fade = min(len(audio), 4 * 48000)
                    audio[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=audio.dtype)[:, None]
                    notes.append("达到长度上限，结尾已淡出")
                config = pipe.effective_config(request, None, sampling)
                seconds = time.perf_counter() - started
                result = SongResult(audio, 48000, semantic, latents, config, pipe.weights,
                                    {"e2e_seconds": seconds, "abc": plan.timing, "semantic": semantic.timing},
                                    identity({"request": request.to_dict(), "config": config, "weights": pipe.weights}))
                receipt = result.save_artifacts(out)
                write_json(out / "studio.json", {"generation_seconds": round(seconds, 1),
                                                  "audio_seconds": round(receipt["audio_seconds"], 1),
                                                  "truncated": receipt["truncated"], "post": notes})
                log(f"[studio] {row['id']} done: {receipt['audio_seconds']:.1f}s audio in {seconds:.1f}s "
                    f"{'; '.join(notes)}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                traceback.print_exc()
                write_json(out / "failure.json", {"id": row["id"], "status": "failed",
                                                  "reason": str(exc), "type": type(exc).__name__})
                if "out of memory" in str(exc).lower():
                    import torch
                    torch.cuda.empty_cache()
    finally:
        pipe.close()
    return 1 if failures == len(rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
