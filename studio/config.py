"""Paths and hardware profile. Everything can be overridden with STUDIO_* environment variables."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
WINDOWS = os.name == "nt"
# Frozen: the exe sits in the install folder. Source: the repo root.
_default_root = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("STUDIO_ROOT", _default_root))
BUNDLE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))  # web/ and studio/flow.json
DATA = Path(os.environ.get("STUDIO_DATA", ROOT / "data"))
MODELS = Path(os.environ.get("STUDIO_MODELS", ROOT / "models"))
HF_HOME = Path(os.environ.get("STUDIO_HF_HOME", ROOT / "hf-cache"))


def _venv(exe, *names):
    """First existing environment among `names` (the single `.venv`, then older two-environment installs)."""
    paths = [ROOT / n / ("Scripts" if WINDOWS else "bin") / (exe + (".exe" if WINDOWS else "")) for n in names]
    return next((p for p in paths if p.exists()), paths[0])


# One environment runs both YuE2 and SheetSage2 (transcriptions are byte-identical to its own env).
YUE2_BIN = Path(os.environ.get("STUDIO_YUE2_BIN", _venv("yue2", ".venv", ".venv-yue2")))
YUE2_PYTHON = Path(os.environ.get("STUDIO_YUE2_PYTHON", _venv("python", ".venv", ".venv-yue2")))
SS2_PYTHON = Path(os.environ.get("STUDIO_SS2_PYTHON", _venv("python", ".venv", ".venv-sheetsage2")))
# abc_tools.py is stdlib-only; run it with any real interpreter (a frozen exe cannot run scripts).
TOOLS_PYTHON = Path(os.environ.get("STUDIO_TOOLS_PYTHON", YUE2_PYTHON if FROZEN else sys.executable))
SKILL_SCRIPTS = Path(os.environ.get("STUDIO_SKILL_SCRIPTS", ROOT / "vendor/YuE/skills/yue2-music/scripts"))
# The installer puts ffmpeg.exe in tools/ffmpeg; SheetSage2 looks it up on PATH, so child processes see it too.
_TOOLS_FFMPEG = ROOT / "tools" / "ffmpeg"
if (_TOOLS_FFMPEG / ("ffmpeg.exe" if WINDOWS else "ffmpeg")).exists():
    os.environ["PATH"] = str(_TOOLS_FFMPEG) + os.pathsep + os.environ.get("PATH", "")
FFMPEG = os.environ.get("STUDIO_FFMPEG", "ffmpeg")
HOST = os.environ.get("STUDIO_HOST", "127.0.0.1")
PORT = int(os.environ.get("STUDIO_PORT", "7860"))
URL = f"http://{HOST}:{PORT}"
NO_WINDOW = subprocess.CREATE_NO_WINDOW if WINDOWS else 0


def gpu():
    """Name, total memory (GiB), driver and compute capability of GPU 0, or None."""
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version,compute_cap",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10,
                             creationflags=NO_WINDOW).stdout.strip().splitlines()[0]
        name, mib, driver, cap = [x.strip() for x in out.split(",")]
        return {"name": name, "memory_gib": round(int(mib) / 1024, 1), "driver": driver, "compute_cap": cap}
    except Exception:
        return None


VRAM_MODES = {"fast": "快速", "save": "省显存"}


def vram_mode():
    """The user's single memory switch (data/settings.json): "fast" (default) or "save"."""
    try:
        import json
        mode = json.loads((DATA / "settings.json").read_text(encoding="utf-8")).get("vram_mode")
    except (OSError, ValueError):
        mode = None
    return mode if mode in VRAM_MODES else "fast"


def fp8_capable(info):
    """YuE2's FP8 kernels need compute capability 8.9+ (RTX 40 / 50 series)."""
    try:
        return tuple(int(x) for x in str(info.get("compute_cap", "0.0")).split(".")) >= (8, 9)
    except (AttributeError, ValueError):
        return False


def auto_profile(info=None, mode=None):
    """Best profile for this GPU. "save" keeps the lossless model but moves it off the GPU between stages."""
    info = info if info is not None else gpu()
    memory = info["memory_gib"] if info else 0
    mode = mode or vram_mode()
    if memory >= 15:
        if mode == "save":
            return "16g-safe"
        return "24g" if memory >= 23 else "16g"
    # 12 GB class: FP8 where the card supports it, otherwise lossless BF16 with offloading (experimental).
    return "12g" if fp8_capable(info) else "12g-safe"


def _complete(model_dir):
    """True when every file in the release's weights_manifest.json is present at its full size."""
    try:
        import json
        manifest = json.loads((model_dir / "weights_manifest.json").read_text())
        # YuE2 releases list {"files": {name: {bytes}}}; MERT-v2 describes its single file at the top level.
        files = manifest.get("files") or {manifest["filename"]: {"bytes": manifest["bytes"]}}
        return all((model_dir / name).stat().st_size == meta["bytes"] for name, meta in files.items())
    except (OSError, ValueError, KeyError):
        return False


def readiness():
    return {
        "yue2_runtime": YUE2_BIN.exists(),
        "sheetsage2_runtime": SS2_PYTHON.exists(),
        "skill_scripts": (SKILL_SCRIPTS / "transcribe.py").exists(),
        "model_yue2": _complete(MODELS / "YuE2-3B"),
        "model_vae": _complete(MODELS / "YuE2-Vae"),
        "model_sheetsage2": (MODELS / "SheetSage2/model.safetensors").exists(),
        "model_mert": _complete(MODELS / "MERT-v2-FullSong"),
        "ffmpeg": shutil.which(FFMPEG) is not None,
    }
