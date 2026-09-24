"""Local HTTP API + static web UI. Run: python -m studio serve"""
from __future__ import annotations

import json
import shutil
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from contextlib import asynccontextmanager

from . import agent, config, flow, mcp_server
from .jobs import Store

store: Store | None = None
mcp_app = mcp_server.http_app()  # creates the session manager the lifespan below runs


@asynccontextmanager
async def lifespan(_app):
    global store
    store = Store()
    async with mcp_server.mcp.session_manager.run():
        yield


app = FastAPI(title="YuE Studio", lifespan=lifespan)
WEB = config.BUNDLE / "web"
SETTINGS = config.DATA / "settings.json"
DEFAULT_SETTINGS = {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "api_key": "", "model": ""}
assistants: dict[str, agent.Assistant] = {}
assistant_lock = threading.Lock()
MCP_URL = f"{config.URL}/agent/mcp"


@app.get("/api/agent/connect")
def agent_connect():
    """Ready-to-paste MCP settings and a hand-off message for any agent."""
    python = str(config.YUE2_PYTHON)
    http_cfg = {"mcpServers": {"yue-studio": {"type": "streamable-http", "url": MCP_URL}}}
    stdio_cfg = {"mcpServers": {"yue-studio": {"command": python, "args": ["-m", "studio", "mcp"], "cwd": str(config.ROOT)}}}
    prompt = (
        "请接入我本机的 MCP 服务「yue-studio」（本地 AI 作曲，基于 YuE2）。\n"
        f"- 首选 Streamable HTTP：{MCP_URL}\n"
        f"- 不支持 HTTP 的话用 stdio：命令 {python}，参数 -m studio mcp，工作目录 {config.ROOT}\n"
        "接入后先用一句话问我想做什么（哼唱变歌 / 文字写歌 / 改编一首歌 / 随便写首歌），"
        "然后调用 wizard_start，再用 wizard_fill 把我说过的都一次填好，只追问真正缺的项，不要一题一题地问；"
        "技术项（版本数、速度、显存）用默认值。收齐后先总结给我确认，再调用 submit_song；生成中可以用 get_job 查进度。"
        "我发的音频附件你那边可能读不到，这时让我在 YuE Studio 窗口里上传，或者给你本机路径。"
        "服务自带完整的使用说明（instructions），请遵守。\n"
        "MCP 配置 JSON：\n" + json.dumps(http_cfg, ensure_ascii=False, indent=2))
    return {"url": MCP_URL, "http_config": http_cfg, "stdio_config": stdio_cfg, "prompt": prompt,
            "tools": [t["name"] for t in agent.TOOLS]}


class FlowStep(BaseModel):
    state: dict | None = None
    answer: object | None = None
    agent: bool = True


class JobIn(BaseModel):
    answers: dict | None = None   # web form: raw answers, turned into a spec here
    spec: dict | None = None      # agent/CLI: spec from `flow` once done
    title: str | None = None


class LyricsIn(BaseModel):
    lyrics: str
    style: str | None = None


@app.get("/api/system")
def system():
    info = config.gpu()
    return {"gpu": info, "auto_profile": config.auto_profile(info), "vram_mode": config.vram_mode(),
            "vram_modes": config.VRAM_MODES, "ready": config.readiness()}


class VramIn(BaseModel):
    mode: str


@app.post("/api/vram_mode")
def set_vram_mode(body: VramIn):
    if body.mode not in config.VRAM_MODES:
        raise HTTPException(400, f"mode must be one of {list(config.VRAM_MODES)}")
    s = load_settings()
    s["vram_mode"] = body.mode
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    return system()


@app.get("/api/flow")
def get_flow():
    return flow.FLOW


@app.post("/api/flow/next")
def flow_next(body: FlowStep):
    state = body.state or flow.new_state(body.agent)
    try:
        if body.answer is not None:
            state = flow.answer(state, body.answer)
        return {"state": state, "question": flow.question(state)}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/preview")
def preview(body: JobIn):
    """Style string and missing steps for the web form, without creating a job."""
    state = {"answers": body.answers or {}, "page": 0, "agent": False}
    missing = flow.pending(state)
    spec = flow.build_spec(state) if not missing else None
    found = flow.detect_language((body.answers or {}).get("lyrics") or (body.answers or {}).get("orig_lyrics"))
    s = load_settings()
    return {"missing": missing, "spec": spec, "lyrics_language": found,
            "lyrics_language_name": flow.LANG_NAMES.get(found), "can_translate": bool(s["api_key"] and s["model"])}


@app.post("/api/upload")
def upload(file: UploadFile):
    suffix = Path(file.filename or "audio.webm").suffix.lower()[:8] or ".bin"
    name = f"uploads/{uuid.uuid4().hex}{suffix}"
    with open(config.DATA / name, "wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"path": name, "filename": file.filename}


def _check_spec(spec):
    if spec.get("audio") and not (config.DATA / spec["audio"]).is_file():
        raise HTTPException(400, f"Uploaded audio not found: {spec['audio']}")
    if spec.get("base_job") and spec["base_job"] not in store.jobs:
        raise HTTPException(400, f"Unknown base job {spec['base_job']}")
    # Checked here (not only in the wizard) because agents may attach lyrics at submit time.
    lang, found = spec.get("language"), flow.detect_language(spec.get("lyrics"))
    if not spec.get("instrumental") and lang in flow.SCRIPT and found and flow.SCRIPT[lang] != flow.SCRIPT[found]:
        raise HTTPException(400, flow.mismatch_message(lang, found))


@app.post("/api/jobs")
def create_job(body: JobIn):
    if body.spec:
        spec = body.spec
    elif body.answers:
        state = {"answers": body.answers, "page": 0, "agent": False}
        missing = flow.pending(state)
        if missing:
            raise HTTPException(400, f"Missing answers: {missing}")
        spec = flow.build_spec(state)
    else:
        raise HTTPException(400, "Provide answers or spec")
    _check_spec(spec)
    return store.create(spec, body.title).view()


@app.get("/api/jobs")
def list_jobs():
    return store.list()


def _job(job_id):
    if job_id not in store.jobs:
        raise HTTPException(404, "No such job")
    return store.jobs[job_id]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    return _job(job_id).view()


@app.post("/api/jobs/{job_id}/lyrics")
def job_lyrics(job_id: str, body: LyricsIn):
    _job(job_id)
    try:
        return store.supply_lyrics(job_id, body.lyrics, body.style).view()
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.post("/api/jobs/{job_id}/cancel")
def job_cancel(job_id: str):
    _job(job_id)
    return store.cancel(job_id).view()


def load_settings():
    try:
        return {**DEFAULT_SETTINGS, **json.loads(SETTINGS.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return dict(DEFAULT_SETTINGS)


class SettingsIn(BaseModel):
    base_url: str
    model: str
    api_key: str | None = None  # None/empty keeps the stored key


class ChatIn(BaseModel):
    session: str = "default"
    message: str = ""


@app.get("/api/assistant/settings")
def get_settings():
    s = load_settings()
    key = s.pop("api_key")
    return {**s, "has_key": bool(key), "key_hint": f"…{key[-4:]}" if len(key) > 8 else ""}


@app.post("/api/assistant/settings")
def put_settings(body: SettingsIn):
    s = load_settings()
    s.update(base_url=body.base_url.strip(), model=body.model.strip())
    if body.api_key:
        s["api_key"] = body.api_key.strip()
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    return get_settings()


@app.post("/api/assistant/chat")
def assistant_chat(body: ChatIn):
    s = load_settings()
    if not (s["api_key"] and s["model"] and s["base_url"]):
        raise HTTPException(400, "请先在「AI 助手 → 设置」里填写接口地址、模型和 API Key")
    with assistant_lock:
        bot = assistants.setdefault(body.session, agent.Assistant())
    try:
        return bot.send(s, body.message)
    except agent.ApiError as exc:
        while bot.messages[-1]["role"] != "user":  # roll back to before this turn so it can be retried
            bot.messages.pop()
        bot.messages.pop()
        raise HTTPException(502, str(exc))


class TranslateIn(BaseModel):
    lyrics: str
    language: str


@app.post("/api/translate_lyrics")
def translate(body: TranslateIn):
    s = load_settings()
    if not (s["api_key"] and s["model"]):
        raise HTTPException(400, "翻译需要大模型：请先在「AI 助手 → 设置」里填好接口、模型和 API Key")
    if body.language not in flow.SCRIPT:
        raise HTTPException(400, "不支持的语言")
    try:
        text = agent.translate_lyrics(s, body.lyrics, body.language)
    except agent.ApiError as exc:
        raise HTTPException(502, str(exc))
    return {"lyrics": text, "detected": flow.detect_language(text)}


@app.post("/api/assistant/reset")
def assistant_reset(body: ChatIn):
    assistants.pop(body.session, None)
    return {"ok": True}


@app.get("/files/{job_id}/{path:path}")
def job_file(job_id: str, path: str):
    base = _job(job_id).dir.resolve()
    target = (base / path).resolve()
    if base not in target.parents or not target.is_file():
        raise HTTPException(404)
    return FileResponse(target)


app.mount("/agent", mcp_app)  # MCP endpoint: /agent/mcp
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
