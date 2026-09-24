"""YuE Studio CLI. Everything except `serve` is standard-library only, so agents can
call it from any Python 3.9+ while the desktop app (or `python -m studio serve`) is running.

  python -m studio serve
  python -m studio flow start --state s.json        # prints the first question
  python -m studio flow fill '{"feature": "text_song", "genre": "pop"}' --state s.json   # many answers at once
  python -m studio flow answer <value> --state s.json
  python -m studio flow back --state s.json
  python -m studio submit --state s.json [--lyrics-file l.txt]
  python -m studio jobs | job <id> [--wait] | lyrics <id> --file l.txt | cancel <id> | system
  python -m studio doctor [--json]                  # installation self-check
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

URL = os.environ.get("STUDIO_URL", "http://127.0.0.1:7860")


def out(data):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=1))


def http(method, path, body=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(URL + path, data=data, method=method,
                                 headers=headers or ({"Content-Type": "application/json"} if body is not None else {}))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Studio server not reachable at {URL} ({e.reason}). Start it: python -m studio serve")


def upload(path):
    path = Path(path)
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return http("POST", "/api/upload", raw=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})["path"]


def load_state(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_flow(args):
    from . import flow
    if args.action == "start":
        state = flow.new_state(agent=True)
    elif args.action == "fill":
        # Several answers at once: flow fill '{"feature": "text_song", "genre": "rnb"}'  (or @answers.json)
        from . import agent
        raw = Path(args.value[1:]).read_text(encoding="utf-8") if (args.value or "").startswith("@") else args.value
        values, errors = json.loads(raw or "{}"), {}
        for key in ("hum_audio", "ref_audio"):
            if values.get(key):
                try:
                    values[key] = agent.resolve_audio(values[key])
                except (ValueError, agent.ApiError) as exc:
                    errors[key] = str(exc)
                    del values[key]
        state, filled, fill_errors, ignored = flow.fill(load_state(args.state) if Path(args.state).exists()
                                                        else flow.new_state(agent=True), values)
        save_state(args.state, state)
        q = flow.question(state)
        q.pop("all_options", None) if not args.all else None
        if q.get("done"):
            q["defaults"] = flow.defaults(state)
        out({"filled": filled, "errors": {**errors, **fill_errors}, "ignored": ignored, "question": q})
        return 1 if errors or fill_errors else None
    else:
        state = load_state(args.state)
        value = flow.BACK if args.action == "back" else args.value
        if args.action == "answer" and value is None:
            raise SystemExit("answer needs a value")
        try:
            state = flow.answer(state, value)
        except ValueError as exc:
            out({"error": str(exc), "question": flow.question(state)})
            return 1
    save_state(args.state, state)
    q = flow.question(state)
    q.pop("all_options", None) if not args.all else None
    out(q)


def compact(job):
    keep = ("id", "title", "status", "stage", "error", "takes", "phrases", "final_style")
    view = {k: job[k] for k in keep if job.get(k)}
    if job.get("status") in ("failed",) and job.get("log_tail"):
        view["log_tail"] = job["log_tail"][-15:]
    view["web"] = f"{URL}/#job={job['id']}"
    return view


def cmd_submit(args):
    from . import flow
    if args.spec:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    else:
        state = load_state(args.state)
        q = flow.question(state)
        if not q["done"]:
            raise SystemExit(f"Flow not finished; next step is {q['step']}")
        spec = q["spec"]
    if args.lyrics_file:
        spec["lyrics"] = Path(args.lyrics_file).read_text(encoding="utf-8")
    if args.style:
        spec["style"] = args.style
    if "write_lyrics" in spec.get("todo", []) and not spec.get("lyrics"):
        raise SystemExit("This job needs lyrics first: write them and pass --lyrics-file")
    if spec.get("audio") and not str(spec["audio"]).startswith("uploads/"):
        spec["audio"] = upload(spec["audio"])
    out(compact(http("POST", "/api/jobs", {"spec": spec, "title": args.title})))


def cmd_job(args):
    deadline = time.time() + args.timeout
    while True:
        job = http("GET", f"/api/jobs/{args.id}")
        if not args.wait or job["status"] not in ("queued", "running") or time.time() > deadline:
            break
        print(f"[{job['status']}] {job.get('stage', '')}", file=sys.stderr, flush=True)
        time.sleep(10)
    out(job if args.full else compact(job))


def cmd_doctor(args):
    """Installation self-check (no server needed). Exit code 0 only when everything required is in place."""
    import shutil
    import subprocess
    from . import config
    checks = []

    def add(name, ok, detail="", required=True):
        checks.append({"check": name, "ok": bool(ok), "detail": detail, "required": required})

    gpu = config.gpu()
    add("NVIDIA 显卡", gpu, f"{gpu['name']} {gpu['memory_gib']} GB，驱动 {gpu['driver']}，算力 {gpu['compute_cap']}" if gpu else "没找到 nvidia-smi")
    if gpu:
        add("显存 ≥ 12 GB", gpu["memory_gib"] >= 11.5, f"自动档位 {config.auto_profile(gpu)}")
    add("Python 环境 (.venv)", config.YUE2_PYTHON.exists(), str(config.YUE2_PYTHON))
    if config.YUE2_PYTHON.exists():
        probe = ("import json, torch; ok = torch.cuda.is_available(); cap = torch.cuda.get_device_capability(0) if ok else (0, 0);"
                 "print(json.dumps({'torch': torch.__version__, 'cuda': ok, 'arch': 'sm_%d%d' % cap,"
                 "'arch_ok': ok and ('sm_%d%d' % cap) in torch.cuda.get_arch_list(), 'bf16': ok and torch.cuda.is_bf16_supported()}))")
        try:
            r = subprocess.run([str(config.YUE2_PYTHON), "-c", probe], capture_output=True, text=True, timeout=180,
                               creationflags=config.NO_WINDOW)
            info = json.loads(r.stdout.strip().splitlines()[-1])
            add("PyTorch 能用显卡", info["cuda"] and info["arch_ok"], f"torch {info['torch']}，{info['arch']}")
            add("BF16", info["bf16"], "" if info["bf16"] else "没有原生 BF16，生成会很慢", required=False)
        except Exception as exc:  # noqa: BLE001
            add("PyTorch 能用显卡", False, f"检查失败：{exc}")
        for mod in ("yue2", "transformers", "mir_eval", "pretty_midi", "fastapi", "webview", "mcp"):
            r = subprocess.run([str(config.YUE2_PYTHON), "-c", f"import {mod}"], capture_output=True, text=True,
                               creationflags=config.NO_WINDOW)
            add(f"依赖 {mod}", r.returncode == 0, (r.stderr.strip().splitlines() or [""])[-1][:160])
    for name, ok in config.readiness().items():
        if name in ("yue2_runtime", "sheetsage2_runtime"):
            continue
        add(name, ok, (shutil.which(config.FFMPEG) or "") if name == "ffmpeg" else "")
    free = shutil.disk_usage(config.ROOT).free / 2**30
    add("磁盘剩余 ≥ 5 GB", free >= 5, f"{free:.0f} GB", required=False)
    for c in checks:
        mark = "✓" if c["ok"] else ("✗" if c["required"] else "!")
        print(f" {mark} {c['check']}  {c['detail']}")
    failed = [c["check"] for c in checks if c["required"] and not c["ok"]]
    if args.json:
        out({"ok": not failed, "failed": failed, "checks": checks})
    print("全部通过" if not failed else f"未通过：{', '.join(failed)}")
    return 1 if failed else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="studio")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve")
    f = sub.add_parser("flow")
    f.add_argument("action", choices=("start", "fill", "answer", "back"))
    f.add_argument("value", nargs="?")
    f.add_argument("--state", default="studio_state.json")
    f.add_argument("--all", action="store_true", help="also print every option, unpaginated")
    s = sub.add_parser("submit")
    s.add_argument("--state", default="studio_state.json")
    s.add_argument("--spec")
    s.add_argument("--lyrics-file")
    s.add_argument("--style")
    s.add_argument("--title")
    sub.add_parser("jobs")
    j = sub.add_parser("job")
    j.add_argument("id")
    j.add_argument("--wait", action="store_true")
    j.add_argument("--timeout", type=int, default=540, help="stop waiting after N seconds (agent tool limits)")
    j.add_argument("--full", action="store_true")
    l = sub.add_parser("lyrics")
    l.add_argument("id")
    l.add_argument("--file", required=True)
    l.add_argument("--style")
    c = sub.add_parser("cancel")
    c.add_argument("id")
    sub.add_parser("system")
    d = sub.add_parser("doctor", help="check the installation (GPU, environment, FFmpeg, models)")
    d.add_argument("--json", action="store_true")
    sub.add_parser("desktop", help="open the desktop window (same as start.bat)")
    sub.add_parser("mcp", help="run the MCP stdio server for external agents")
    sub.add_parser("tools", help="print the agent tool schemas (OpenAI function format) and system prompt")
    args = p.parse_args(argv)

    if args.cmd == "desktop":
        from .desktop import main as desktop
        desktop()
    elif args.cmd == "mcp":
        from .mcp_server import main as mcp_main
        mcp_main()
    elif args.cmd == "tools":
        from . import agent
        out({"system_prompt": agent.SYSTEM_PROMPT, "tools": agent.openai_tools()})
    elif args.cmd == "serve":
        import uvicorn
        from . import config
        print(f"YuE Studio → http://{config.HOST}:{config.PORT}")
        uvicorn.run("studio.server:app", host=config.HOST, port=config.PORT, log_level="warning")
    elif args.cmd == "flow":
        return cmd_flow(args)
    elif args.cmd == "submit":
        cmd_submit(args)
    elif args.cmd == "jobs":
        out([{k: j.get(k) for k in ("id", "title", "status", "stage")} for j in http("GET", "/api/jobs")])
    elif args.cmd == "job":
        cmd_job(args)
    elif args.cmd == "lyrics":
        text = Path(args.file).read_text(encoding="utf-8")
        out(compact(http("POST", f"/api/jobs/{args.id}/lyrics", {"lyrics": text, "style": args.style})))
    elif args.cmd == "cancel":
        out(compact(http("POST", f"/api/jobs/{args.id}/cancel", {})))
    elif args.cmd == "system":
        out(http("GET", "/api/system"))
    elif args.cmd == "doctor":
        sys.stdout.reconfigure(encoding="utf-8")
        return cmd_doctor(args)


if __name__ == "__main__":
    raise SystemExit(main())
