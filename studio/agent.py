"""Model-agnostic agent tools over the local YuE Studio API.

Used by the in-app assistant (any OpenAI-compatible chat API, e.g. Doubao/Volcengine Ark)
and by the MCP server (Trae, Coze, Cursor, Claude...). Nothing here is tied to one vendor.
"""
from __future__ import annotations

import json
import mimetypes
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from . import config, flow

SYSTEM_PROMPT = """你是 YuE Studio 的作曲助手，帮用户在本地显卡上用 YuE2 模型做歌。
做法是"先听需求，一次填好，只问缺的"，不要像问卷一样一题一题问。

流程：
1. 开场只问一句开放式的问题，附一行例子，例如：
   "想做点什么？比如：哼一段旋律变成歌 / 给我一段歌词或主题写成歌 / 拿一首歌换词或换风格 / 或者你说'随便写首歌'我来定。"
   不要先让用户选"类别"再选"功能"。
2. 用户说完后调用 wizard_start（拿到功能列表和每个功能要填的项），再调用一次 wizard_fill，
   把用户这句话里能确定的都填进去（feature 必填；曲风、情绪、人声、语言、主题等能推断就填）。
   - 用户说"随便/你定/都行"的项，你直接替他选合适的值填上，不要再问。
   - 用户没提语言：歌词由你写时默认 zh（普通话）；用户自己给了歌词就不用填语言（自动识别）。
   - 版本数、速度、显存、规划模式这些技术项不用问，用默认值；用户主动提到时才填（variants、tempo 等）。
3. wizard_fill 返回的 next 就是真正还缺的一项。问的时候一句话问清楚，从 options 里挑 3~5 个最相关的给用户参考
   （不要把几十个选项全列出来），并说明也可以直接说想法。拿到回答再调用 wizard_fill（可以一次填多项）。
   value 用选项的 value；custom_allowed 为 true 时也可以直接填英文风格描述。用户说"上一步/返回"时调用 wizard_back。
4. 音频文件（哼唱 / 参考歌曲）：value 可以是本机绝对路径、uploads/...，或能直接下载的 http(s) 链接，填进去时会立即检查。
   聊天软件里发的附件在聊天平台上，YuE Studio 读不到：如果报"找不到文件"，请用户在 YuE Studio 窗口里上传或录音，
   或者把文件在电脑上的完整路径发给你。
5. 作品类的项（精修要选之前的作品）：先调用 list_jobs，把已完成的作品列给用户选。
6. 返回 done=true 后，用 3~5 行总结：功能、风格描述(style)、歌词来源，以及 defaults 里的默认值
   （"默认出 1 个版本，要改直接说"），问"开始生成吗？"。确认后调用 submit_song。
6. spec.todo 含 write_lyrics：你根据 theme 和 structure 写歌词，先给用户看，确认后通过 submit_song 的 lyrics 参数提交。
   含 write_lyrics_after_transcription：直接 submit_song；任务扒谱后状态变为 needs_lyrics，
   用 get_job 取 phrases：sections 按顺序一段对一段，段内 lines 每一项写一句歌词，
   中文每句字数≈该项 notes（一字一音，可 ±1），英文按音节数对齐，
   给用户确认后调用 provide_lyrics。
7. 歌词格式：[Verse] [Pre-Chorus] [Chorus] [Bridge] [Outro] 标签单独一行，每句一行，段落间空一行；不要写舞台说明或和弦。
   模型唱的就是歌词本身：用户选了日语就必须写（或把用户的歌词翻译成）日语歌词，选英语就写英语，
   否则 submit_song 会报"语言不一致"。官方只支持中文和英文，粤语、日语、韩语是实验性的，要提前告诉用户。
8. 生成大约需要 1~4 分钟（16GB 显卡上，3 分钟的歌约 3 分钟），提交后告诉用户可以在右侧作品列表试听；用户问进度时调用 get_job（有 progress 字段）。
9. 时长：纯音乐的"多长"会按整段裁剪乐谱，大致做到；带歌词的歌长度由歌词决定（每 4 句约 25~35 秒），
   哼唱/参考歌曲跟随原音频长度。不要承诺精确到秒。你写词时按用户要的长度控制句数。
10. 失败时读 error；显存不足先建议关掉其他占显存的程序，或在窗口顶部切到"省显存"，不要偷偷缩短歌曲。
11. 预设：曲风 61 种、情绪 17 种、人声 20 种、主奏乐器 18 种。对不上时调用 style_reference(section="presets", keyword=...)
   找 value；预设里没有就按官方写法自己写英文风格描述作为自由文本（参考 style_reference 的 rules 和 official），
   例如"曲风 + 核心乐器 + 情绪 + 人声音色/唱法 + 速度感 + 制作质感"，不要写真实歌手名。
   预设没覆盖的细节（如"前奏只有钢琴，副歌加弦乐"）填到 extra。
12. 纯音乐和哼唱 → 纯音乐：模型偶尔仍会带一点哼唱，这是模型本身的限制。哼唱 → 纯音乐要哼 20 秒以上（太短会报错），
   默认出 4 个版本让用户挑。
13. 完成后主动问要不要精修：改速度、换风格、改词或手动改谱（wizard_start 后 wizard_fill 填 feature=remix 和 base_job）。
14. 改编他人歌曲只供个人使用。回答简洁、口语化，用中文。"""

TOOLS = [
    {"name": "wizard_start", "description": "开始一首新歌（或精修）。返回全部功能及每个功能要填的项，之后用 wizard_fill 一次填好。",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "wizard_fill", "description": "一次填多项，例如 {\"feature\": \"text_song\", \"genre\": \"rnb\", \"mood\": \"sad\", "
                                           "\"language\": \"yue\"}。返回已填、出错、忽略的项，以及真正还缺的下一项（next），"
                                           "全部填完时 next.done=true 并带 spec 和 defaults。",
     "parameters": {"type": "object", "properties": {
         "answers": {"type": "object", "description": "项名 → 值。值用选项的 value，也可以是自由文本、文件路径/链接、数字或歌词全文",
                     "additionalProperties": {"type": "string"}}},
                    "required": ["answers"]}},
    {"name": "wizard_answer", "description": "只回答当前这一项（等同于 wizard_fill 只填 next.step）。",
     "parameters": {"type": "object", "properties": {"value": {"type": "string", "description": "选项的 value、自由文本、文件路径、数字或歌词全文"}},
                    "required": ["value"]}},
    {"name": "wizard_back", "description": "撤销上一个回答，回到上一题。",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "submit_song", "description": "向导完成后提交生成任务。",
     "parameters": {"type": "object", "properties": {
         "title": {"type": "string", "description": "给这首歌起的名字"},
         "lyrics": {"type": "string", "description": "AI 写好的歌词（todo 含 write_lyrics 时必填）"},
         "style": {"type": "string", "description": "可选：覆盖风格描述"}}}},
    {"name": "get_job", "description": "查询任务状态、生成结果、扒谱得到的 phrases。",
     "parameters": {"type": "object", "properties": {
         "job_id": {"type": "string"},
         "wait_seconds": {"type": "integer", "description": "最多等待多少秒直到任务不再排队/运行（0~50）"}},
                    "required": ["job_id"]}},
    {"name": "list_jobs", "description": "列出所有作品及状态。", "parameters": {"type": "object", "properties": {}}},
    {"name": "provide_lyrics", "description": "给状态为 needs_lyrics 的任务补上歌词并继续生成。",
     "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}, "lyrics": {"type": "string"}},
                    "required": ["job_id", "lyrics"]}},
    {"name": "cancel_job", "description": "取消排队或运行中的任务。",
     "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}},
    {"name": "style_reference", "description": "查风格描述参考：官方演示的写法、段落标签、本软件全部预设。"
                                               "用户想要的效果预设里没有、或要自己写 style 时先查。",
     "parameters": {"type": "object", "properties": {
         "section": {"type": "string", "enum": ["rules", "presets", "official", "covers"],
                     "description": "rules=写法要点和段落标签；presets=全部预设及 value；official=官方演示的风格描述；covers=官方改编演示"},
         "keyword": {"type": "string", "description": "可选：只看含这个词的条目，如 jazz、ballad、古风、女声"}},
                    "required": ["section"]}},
]


class ApiError(Exception):
    pass


def http(method, path, body=None, raw=None, headers=None, base=None, timeout=60):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request((base or config.URL) + path, data=data, method=method,
                                 headers=headers or ({"Content-Type": "application/json"} if body is not None else {}))
    # Never route the local API through a system proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ApiError(f"HTTP {e.code}: {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        raise ApiError(f"YuE Studio 没有在运行（{config.URL}）：{e.reason}")


def upload(path):
    path = Path(path)
    if not path.is_file():
        raise ApiError(f"找不到文件 {path}")
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: {ctype}\r\n\r\n").encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return http("POST", "/api/upload", raw=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})["path"]


def feature_overview():
    """Every feature with the items an agent fills (technical ones default and are left out)."""
    out = []
    for key, f in flow.FLOW["features"].items():
        steps = {}
        for s in f["steps"]:
            info = flow.step_def(s)
            if info.get("agent_skip"):
                continue
            entry = info["q"].split("（")[0][:40]
            if info["type"] == "choice" and len(info.get("options", [])) <= 8:
                entry += "：" + " / ".join(o["value"] for o in info["options"] if not o.get("only") or key in o["only"])
            elif info["type"] == "choice":
                entry += f"（{len(info['options'])} 个预设，可自由描述）"
            steps[s] = entry
        out.append({"feature": key, "label": f["label"], "desc": f["desc"], "fields": steps})
    return out


MAX_AUDIO_BYTES = 100 * 1024 * 1024


def resolve_audio(value):
    """A hum / reference answer must be a file YuE Studio can read: upload it now, not at submit time."""
    value = str(value).strip().strip('"')
    if value.startswith("uploads/"):
        if (config.DATA / value).is_file():
            return value
        raise ValueError(f"找不到已上传的文件 {value}，请重新上传")
    if re.match(r"https?://", value, re.I):
        return upload_url(value)
    path = Path(value)
    if path.is_absolute() and path.is_file():
        return upload(path)
    raise ValueError(f"找不到文件“{value}”。聊天软件里的附件存放在聊天平台上，YuE Studio 读不到。"
                     "请在 YuE Studio 窗口里上传或录音，或者把文件在这台电脑上的完整路径（如 E:\\Music\\hum.mp3）发过来，"
                     "或者给一个能直接下载的链接。")


def upload_url(url):
    import tempfile
    name = Path(urllib.parse.urlparse(url).path).name or "audio"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "YuEStudio"}), timeout=60) as r:
            data = r.read(MAX_AUDIO_BYTES + 1)
    except (urllib.error.URLError, ValueError) as exc:
        raise ValueError(f"下载不了这个链接：{exc}")
    if len(data) > MAX_AUDIO_BYTES:
        raise ValueError("文件超过 100MB，请剪短一些")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / (name if Path(name).suffix else name + ".mp3")
        path.write_bytes(data)
        return upload(path)


def compact_job(job):
    keep = ("id", "title", "status", "stage", "error", "takes", "phrases", "final_style")
    view = {k: job[k] for k in keep if job.get(k)}
    if job.get("progress"):
        p = job["progress"]
        view["progress"] = {k: p[k] for k in ("phase", "percent", "detail", "take") if p.get(k) is not None}
    if job.get("status") == "failed" and job.get("log_tail"):
        view["log_tail"] = job["log_tail"][-12:]
    return view


class Session:
    """One conversation's wizard state; tools are executed against the local HTTP API."""

    def __init__(self):
        self.state = None

    def question(self):
        if self.state is None:
            return None
        q = flow.question(self.state, page_size=None)  # chat agents get every option at once
        if q.get("done"):
            q["defaults"] = flow.defaults(self.state)
        return q

    def call(self, name, args):
        try:
            return getattr(self, "t_" + name)(**(args or {}))
        except (ApiError, ValueError, TypeError) as exc:
            return {"error": str(exc), "next": self.question()}

    def t_wizard_start(self):
        self.state = flow.new_state(agent=True)
        return {"features": feature_overview(), "next": "用 wizard_fill 一次填好：feature 加上用户已经说清楚的项"}

    def t_wizard_fill(self, answers):
        if isinstance(answers, str):
            answers = json.loads(answers)
        if self.state is None:
            self.state = flow.new_state(agent=True)
        answers, file_errors = dict(answers), {}
        for key in ("hum_audio", "ref_audio"):
            if answers.get(key):
                try:
                    answers[key] = resolve_audio(answers[key])
                except (ValueError, ApiError) as exc:  # keep the rest of the answers
                    file_errors[key] = str(exc)
                    del answers[key]
        self.state, filled, errors, ignored = flow.fill(self.state, answers)
        errors = {**file_errors, **errors}
        result = {"filled": {k: self.state["answers"][k] for k in filled if k not in ("lyrics", "orig_lyrics", "abc")}}
        if errors:
            result["errors"] = errors
        if ignored:
            result["ignored"] = {k: "这个功能没有这一项，或者要先填好前面的项" for k in ignored}
        result["next"] = self.question()
        return result

    def t_wizard_answer(self, value):
        if self.state is None:
            self.state = flow.new_state(agent=True)
        step = flow.pending(self.state)[0] if flow.pending(self.state) else None
        if step in ("hum_audio", "ref_audio"):
            value = resolve_audio(value)
        self.state = flow.answer(self.state, value)
        return self.question()

    def t_wizard_back(self):
        if self.state is None:
            raise ValueError("向导还没开始")
        self.state = flow.answer(self.state, flow.BACK)
        return self.question()

    def t_submit_song(self, title=None, lyrics=None, style=None):
        q = self.question()
        if not q or not q.get("done"):
            raise ValueError(f"向导还没完成，下一题是 {q and q.get('step')}")
        spec = dict(q["spec"])
        if lyrics:
            spec["lyrics"] = flow.normalize_lyrics(lyrics)
        if style:
            spec["style"] = style
        if "write_lyrics" in spec.get("todo", []) and not spec.get("lyrics"):
            raise ValueError("这首歌需要先写好歌词，通过 lyrics 参数传入")
        if spec.get("audio") and not str(spec["audio"]).startswith("uploads/"):
            spec["audio"] = upload(spec["audio"])
        job = http("POST", "/api/jobs", {"spec": spec, "title": title})
        self.state = None
        return compact_job(job)

    def t_get_job(self, job_id, wait_seconds=0):
        deadline = time.time() + max(0, min(int(wait_seconds or 0), 50))
        while True:
            job = http("GET", f"/api/jobs/{job_id}")
            if job["status"] not in ("queued", "running") or time.time() >= deadline:
                return compact_job(job)
            time.sleep(3)

    def t_list_jobs(self):
        return [{k: j.get(k) for k in ("id", "title", "status", "stage")} for j in http("GET", "/api/jobs")]

    def t_provide_lyrics(self, job_id, lyrics):
        return compact_job(http("POST", f"/api/jobs/{job_id}/lyrics", {"lyrics": lyrics}))

    def t_cancel_job(self, job_id):
        return compact_job(http("POST", f"/api/jobs/{job_id}/cancel", {}))

    def t_style_reference(self, section, keyword=None):
        return {"section": section, "text": style_reference(section, keyword)}


GUIDE_SECTIONS = {"rules": ("## 1.", "## 2."), "presets": ("## 3.",), "official": ("## 4.",), "covers": ("## 5.",)}


def style_reference(section, keyword=None):
    """A slice of studio/style_guide.md; with a keyword, only the matching rows/items under their headings."""
    if section not in GUIDE_SECTIONS:
        raise ValueError(f"section 只能是 {', '.join(GUIDE_SECTIONS)}")
    text = (config.BUNDLE / "studio" / "style_guide.md").read_text(encoding="utf-8")
    body = "".join(c for c in re.split(r"(?m)^(?=## )", text) if c.startswith(GUIDE_SECTIONS[section]))
    if keyword:
        kw, keep, heads, whole = keyword.lower(), [], [], False
        for ln in body.splitlines():
            if ln.startswith("#"):
                heads, whole = [ln], kw in ln.lower()  # a matching heading keeps its whole block
            elif ln.startswith(("|---", "| value")):
                heads.append(ln)
            elif ln.strip() and (whole or kw in ln.lower()):
                keep += heads + [ln]
                heads = []
        body = "\n".join(keep) or f"没有含“{keyword}”的条目，换个词或去掉 keyword 看全部。"
    return body[:12000]


def openai_tools():
    return [{"type": "function", "function": t} for t in TOOLS]


def translate_lyrics(settings, lyrics, language):
    """Singable translation keeping section tags and line structure (used by the manual form)."""
    target = {"zh": "简体中文普通话", "yue": "粤语（用粤语口语用字）", "en": "English", "ja": "日本語", "ko": "한국어"}[language]
    messages = [
        {"role": "system", "content": "你是歌词译配。把歌词译成目标语言，要能唱：保留每个 [段落标签] 原样和位置，"
                                      "行数与原文一致、一行对一行，每行音节数尽量接近原文，押韵自然。只输出译好的歌词，不要解释。"},
        {"role": "user", "content": f"目标语言：{target}\n\n{lyrics}"}]
    text = chat_completion(settings, messages, tools=False).get("content") or ""
    return re.sub(r"^```\w*\n|\n```$", "", text.strip())


def chat_completion(settings, messages, tools=True):
    """POST {base_url}/chat/completions (OpenAI-compatible; Doubao Ark, DeepSeek, Qwen...)."""
    body = {"model": settings["model"], "messages": messages, "temperature": 0.4,
            **({"tools": openai_tools()} if tools else {})}
    req = urllib.request.Request(settings["base_url"].rstrip("/") + "/chat/completions",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {settings['api_key']}"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())["choices"][0]["message"]
    except urllib.error.HTTPError as e:
        raise ApiError(f"大模型接口返回 {e.code}: {e.read().decode(errors='replace')[:400]}")
    except urllib.error.URLError as e:
        raise ApiError(f"连不上大模型接口：{e.reason}")


class Assistant:
    """Tool-calling loop for the in-app chat panel."""

    def __init__(self):
        self.session = Session()
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def send(self, settings, text, max_rounds=12):
        self.messages.append({"role": "user", "content": text})
        used = []
        for _ in range(max_rounds):
            msg = chat_completion(settings, self.messages)
            calls = msg.get("tool_calls") or []
            self.messages.append({"role": "assistant", "content": msg.get("content") or "",
                                  **({"tool_calls": calls} if calls else {})})
            if not calls:
                return {"reply": msg.get("content") or "", "tools": used, "question": self.session.question()}
            for call in calls:
                fn = call["function"]
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                if fn["name"] == "get_job":
                    args["wait_seconds"] = min(int(args.get("wait_seconds") or 0), 5)  # keep the chat responsive
                result = self.session.call(fn["name"], args) if any(t["name"] == fn["name"] for t in TOOLS) \
                    else {"error": f"unknown tool {fn['name']}"}
                used.append(fn["name"])
                self.messages.append({"role": "tool", "tool_call_id": call["id"],
                                      "content": json.dumps(result, ensure_ascii=False)})
        return {"reply": "（工具调用轮数过多，已暂停，请再说一句继续）", "tools": used, "question": self.session.question()}
