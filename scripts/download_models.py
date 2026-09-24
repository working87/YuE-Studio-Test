"""Download model weights (about 10 GB). Default source: ModelScope (China, no proxy needed).

Resumable (HTTP Range) and size-checked; rerun if interrupted. The ModelScope copies are byte-identical to the
Hugging Face releases (MERT-v2 included, at the revision SheetSage2 pins).
  python scripts/download_models.py [--source modelscope|hf] [--skip-transcription]
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# MERT-v2 goes to models/ too; the pipeline hands it to SheetSage2 as --base-model.
MODELS = [("m-a-p/YuE2-Vae", "models/YuE2-Vae"), ("m-a-p/SheetSage2", "models/SheetSage2"),
          ("m-a-p/MERT-v2-FullSong", "models/MERT-v2-FullSong"), ("m-a-p/YuE2-3B", "models/YuE2-3B")]
SKIP = ("assets/", ".whl")
DIRECT = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # domestic source: bypass proxies
PROXIED = urllib.request.build_opener()


def modelscope_files(repo):
    url = f"https://www.modelscope.cn/api/v1/models/{repo}/repo/files?Recursive=true"
    files = json.loads(DIRECT.open(url, timeout=30).read())["Data"]["Files"]
    return [(f["Path"], f.get("Size"), f"https://www.modelscope.cn/models/{repo}/resolve/master/{urllib.parse.quote(f['Path'])}")
            for f in files if f.get("Type") != "tree"]


def hf_files(repo):
    data = json.loads(PROXIED.open(f"https://huggingface.co/api/models/{repo}?blobs=true", timeout=30).read())
    return [(s["rfilename"], s.get("size"), f"https://huggingface.co/{repo}/resolve/main/{s['rfilename']}")
            for s in data["siblings"]]


def fetch(url, dest, size, opener):
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 31):
        have = dest.stat().st_size if dest.exists() else 0
        if size is not None and have == size:
            return
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
            with opener.open(req, timeout=60) as r, open(dest, "ab" if have and r.status == 206 else "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            if size is None:
                return
        except Exception as exc:  # noqa: BLE001
            print(f"   {dest.name}: attempt {attempt} failed ({type(exc).__name__}); resuming", flush=True)
            time.sleep(min(5 * attempt, 30))
    raise SystemExit(f"Giving up on {dest}")


def main():
    source = sys.argv[sys.argv.index("--source") + 1] if "--source" in sys.argv else "modelscope"
    skip_audio = "--skip-transcription" in sys.argv
    for repo, local in MODELS:
        if skip_audio and ("SheetSage" in repo or "MERT" in repo):
            continue
        print(f"== {repo}", flush=True)
        try:
            files, opener = (modelscope_files(repo), DIRECT) if source == "modelscope" else (hf_files(repo), PROXIED)
        except Exception as exc:  # noqa: BLE001
            # No silent fallback to Hugging Face: it is usually unreachable from China without a proxy.
            raise SystemExit(f"   无法从 {source} 获取 {repo} 的文件列表（{exc}）。请检查网络后重新运行，已下载的部分会续传；"
                             f"能访问 Hugging Face 的话也可以加 --source hf")
        for path, size, url in files:
            if any(s in path for s in SKIP):
                continue
            fetch(url, ROOT / local / path, size, opener)
        print(f"   -> {ROOT / local}", flush=True)
    print("ALL MODELS DONE", flush=True)


if __name__ == "__main__":
    main()
