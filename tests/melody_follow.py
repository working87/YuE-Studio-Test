"""Does the output follow the hummed melody? Transcribe the output and compare pitch-class contours.

    .venv\\Scripts\\python.exe tests\\melody_follow.py <job_id> [<job_id> ...]
Score: best share of 0.1 s frames (over key transposition and a ±3 s offset) where the output's melody
pitch class equals the hummed one, counted over the hummed frames. Random melodies land around 0.1–0.2.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor/YuE/skills/yue2-music/scripts")]
sys.stdout.reconfigure(encoding="utf-8")
from abc_tools import parse_abc  # noqa: E402

STEP = 0.1


def roll(abc, voice=None):
    """Pitch per 0.1 s frame (-1 = silence) of the voice with the most notes."""
    score = parse_abc(abc)
    bpm = int(re.search(r"^Q:\s*1/4\s*=\s*(\d+)", abc, re.M).group(1))
    name = voice or max(score.voices, key=lambda v: len(score.voices[v].notes))
    notes = score.voices[name].notes
    if not notes:
        return np.array([])
    sec = 60 / bpm
    end = max(float(o + d) for o, p, d in notes) * sec
    frames = np.full(int(end / STEP) + 1, -1)
    for onset, pitch, dur in notes:
        a, b = int(float(onset) * sec / STEP), int(float(onset + dur) * sec / STEP)
        frames[a:b] = pitch
    return frames


def transcribe(audio, tag):
    work = ROOT / "tests" / "follow_check" / tag
    if not (work / "score.abc").exists():
        wav = work.with_suffix(".wav")
        work.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio), "-ac", "1", "-ar", "44100",
                        "-af", "apad=pad_dur=2", str(wav)], check=True)
        subprocess.run([sys.executable, str(ROOT / "vendor/YuE/skills/yue2-music/scripts/transcribe.py"), str(wav),
                        "--task", "melody-full", "--output", str(work), "--model", str(ROOT / "models/SheetSage2")],
                       capture_output=True, env={**os.environ, "HF_HOME": str(ROOT / "hf-cache"), "PYTHONUTF8": "1"})
    return (work / "score.abc").read_text(encoding="utf-8")


def follow(hum, out):
    voiced = np.where(hum >= 0)[0]
    best = 0.0
    for lag in range(-int(3 / STEP), int(3 / STEP) + 1):
        idx = voiced + lag
        ok = (idx >= 0) & (idx < len(out))
        if ok.sum() < len(voiced) * 0.5:
            continue
        h, o = hum[voiced[ok]], out[idx[ok]]
        sung = o >= 0
        for shift in range(12):
            best = max(best, float(np.sum(sung & (((o - h + shift) % 12) == 0)) / len(voiced)))
    return best


for job_id in sys.argv[1:]:
    d = ROOT / "data/jobs" / job_id
    hum = roll((d / "score.abc").read_text(encoding="utf-8"))
    for take in sorted((d / "takes").glob("take-*")):
        for name in ("audio.flac", "audio_with_vocals.flac", "audio_devocal.flac"):
            if (take / name).exists():
                out = roll(transcribe(take / name, f"{job_id}-{take.name}-{name}"))
                print(f"{job_id} {take.name} {name:24} hum {len(hum) * STEP:.1f}s, output melody {len(out) * STEP:.1f}s, "
                      f"melody follow {follow(hum, out):.0%}", flush=True)
