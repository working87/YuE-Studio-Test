# AGENTS.md — deploying and using YuE Studio

Instructions for coding agents (Claude Code, Cursor, Codex, Trae, …) asked to install or run this project on a
user's Windows PC. Talk to the user in their language (usually Chinese). Every download goes through mainland-China
mirrors; do not switch to GitHub / Hugging Face / pytorch.org unless the user explicitly asks.

## 0. Ground rules

- Windows 10/11 x64 + NVIDIA GPU only. All commands below are PowerShell, run from the repository root.
- Everything installs **inside the repo folder** (`tools\`, `.venv\`, `models\`). Never install Python, CUDA,
  FFmpeg or anything else system-wide, and never change system settings or PATH.
- The user does **not** need CUDA Toolkit: the torch wheels bundle the CUDA 12.8 runtime. Only the NVIDIA driver matters.
- Installed size ~15 GB (models 9.8 GB + `.venv` 4.7 GB + `tools` 0.2 GB). During installation ~20 GB free is
  needed: uv's ~5 GB download cache lives in `tools\uv-cache` and is cleared after a successful install
  (kept after a failure so a re-run resumes). Check free space first and tell the user before starting.
- Do not modify `vendor/YuE` (official code, patched at install time by `scripts\patch_windows.py`).

## 1. Detect the GPU and decide

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\detect_gpu.ps1 -Json
```

Output (one JSON line): `ok`, `tier`, `profile`, `level` (`ok` / `warn` / `error`), `message` (Chinese, show it to
the user), `gpu` {name, memory_gb, driver, compute_cap}. Exit code 1 when `ok` is false.

| Condition | Decision |
|---|---|
| no `nvidia-smi` | stop: no NVIDIA GPU/driver. Point to https://www.nvidia.cn/drivers |
| driver major < 570 | stop: ask the user to update the driver, then re-run detection |
| compute capability < 7.0 (GTX 10 series and older) | stop: not supported by PyTorch 2.10 |
| memory < 11.5 GB | stop: not supported; mention the community GGUF ports listed in README "8GB 显卡" (not integrated) |
| 11.5–15 GB | install, but warn it is slow/experimental (`12g` with FP8 on compute ≥ 8.9, else `12g-safe`) |
| 15–23 GB | install (`16g`, tested on RTX 5070 Ti 16GB) |
| ≥ 23 GB | install (`24g`) |
| compute 7.x | install only after warning: no native BF16, untested, may be very slow |

Only continue past a stop condition if the user explicitly insists (then pass `-Force` to the installer).
Nothing needs configuring per GPU: the app picks the profile at run time from the same rules
(`studio/config.py:auto_profile`); the user only has a 快速/省显存 switch in the window.

## 2. Install

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
```

Steps it performs (all idempotent; re-running resumes):

1. GPU detection (as above; aborts on `ok=false` unless `-Force`)
2. `tools\uv\uv.exe` from the Tsinghua PyPI mirror (wheel `uv-0.12.18-py3-none-win_amd64.whl`)
3. Python 3.12 from npmmirror (`UV_PYTHON_INSTALL_MIRROR`) into `tools\python`, venv `.venv`,
   `requirements.txt` from Tsinghua PyPI + torch/torchaudio 2.10.0+cu128 from `https://mirrors.aliyun.com/pytorch-wheels/cu128/`,
   then `scripts\patch_windows.py`
4. `tools\ffmpeg\ffmpeg.exe` copied out of the `imageio-ffmpeg` wheel
5. PyTorch CUDA check
6. `scripts\download_models.py` → `models\YuE2-3B`, `YuE2-Vae`, `SheetSage2`, `MERT-v2-FullSong` from ModelScope
   (size-checked, resumable; `-ModelSource hf` only if the user can reach Hugging Face)
7. `python -m studio doctor`

Options: `-SkipModels` (environment only), `-Force` (ignore a failed GPU check), `-ModelSource modelscope|hf`.
The full log is `install.log`. The installer can take 10–30 minutes, mostly the torch wheel and the models;
run it in the background / with a long timeout and report progress from `install.log`.

## 3. Verify

```powershell
.venv\Scripts\python.exe -m studio doctor --json
```

`ok: true` means GPU, PyTorch CUDA, every dependency, FFmpeg and all four models are in place.
Report any `failed` item to the user with its `detail`.

Optional end-to-end check (needs the app running, takes ~1 minute on a 16 GB card):
start `start.bat`, then use the MCP tools or `python -m studio flow fill …` + `submit` (see below) to make a short song.

## 4. Troubleshooting

| Symptom | Fix |
|---|---|
| `Invoke-WebRequest` / uv timeouts | network hiccup: re-run `install.ps1` (resumes) |
| `torch.cuda.is_available()` is False | driver too old or no NVIDIA GPU; update driver ≥ 570 |
| `sm_XX` not in arch list | GPU too old for PyTorch 2.10 (see table) |
| model download stops | re-run; files are resumed and size-checked |
| out of GPU memory while generating | close other GPU programs or switch to 省显存 in the window; the app already retries with offloading |
| PowerShell shows garbled Chinese | the `.ps1` files must stay UTF-8 **with BOM** (Windows PowerShell 5.1) |

## 5. Running and using it

- Start: `start.bat` (desktop window) — or `.venv\Scripts\python.exe -m studio serve` for the API only (port 7860).
- MCP (Streamable HTTP, while the app runs): `http://127.0.0.1:7860/agent/mcp`.
  stdio: command `<repo>\.venv\Scripts\python.exe`, args `-m studio mcp`, cwd `<repo>`.
- Tools: `wizard_start` → `wizard_fill` (fill everything the user already said in one call) → ask only what `next`
  says is missing → confirm → `submit_song` → `get_job`. The MCP server's instructions contain the full conversation
  rules; follow them. `style_reference` looks up presets and the official style-prompt examples.
- Claude Code users: the skill in `.claude/skills/yue-studio/SKILL.md` drives the CLI (`python -m studio flow fill …`).
- Audio files must be on this PC (absolute path or an http(s) link); chat attachments on a remote chat platform are
  not readable — ask the user to upload in the YuE Studio window instead.

## 6. For contributors

- Unit tests (no GPU): `.venv\Scripts\python.exe tests\test_language.py` (and the other `tests\test_*.py`,
  `tests\mapping_audit.py`). `tests\test_agent_fill.py` also exercises uploads when the app is running.
- Presets live in `studio/flow.json` (regenerate with `scripts/build_presets.py`); the agent style reference
  `studio/style_guide.md` is generated by `scripts/build_style_guide.py`.
- Keep `.ps1` files UTF-8 with BOM; keep every download on a domestic mirror.
