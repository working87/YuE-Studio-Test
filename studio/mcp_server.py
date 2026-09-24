"""MCP server exposing the same tools as the in-app assistant.

Two transports, same tools:
  * Streamable HTTP, served by the desktop app itself at  http://127.0.0.1:7860/agent/mcp
    (agents only need the URL; the app must be open).
  * stdio:  <install>\\.venv\\Scripts\\python.exe -m studio mcp
    (for clients without HTTP support; starts the desktop app if it is not running).
Each MCP client session gets its own wizard state.
"""
from __future__ import annotations

import json
import subprocess
import time

import anyio
from mcp.server.fastmcp import Context, FastMCP

from . import agent, config

mcp = FastMCP("yue-studio", instructions=agent.SYSTEM_PROMPT)
sessions: dict[int, agent.Session] = {}
STDIO = False
NEEDS_APP = {"wizard_fill", "wizard_answer", "submit_song", "get_job", "list_jobs", "provide_lyrics", "cancel_job"}


def ensure_app():
    """stdio mode only: the desktop app owns the GPU queue, so start it if needed."""
    try:
        agent.http("GET", "/api/system", timeout=5)
        return
    except agent.ApiError:
        pass
    exe = config.ROOT / "YuEStudio.exe"
    cmd = [str(exe)] if exe.exists() else [str(config.YUE2_PYTHON), "-m", "studio", "desktop"]
    subprocess.Popen(cmd, cwd=config.ROOT)
    for _ in range(60):
        time.sleep(1)
        try:
            agent.http("GET", "/api/system", timeout=3)
            return
        except agent.ApiError:
            continue


async def run(ctx: Context, name: str, **args) -> str:
    session = sessions.setdefault(id(ctx.session), agent.Session())

    def work():
        if STDIO and name in NEEDS_APP:
            ensure_app()
        return session.call(name, args)

    # Tools call the app's HTTP API; in HTTP mode that is this same server, so never block its event loop.
    return json.dumps(await anyio.to_thread.run_sync(work), ensure_ascii=False)


@mcp.tool()
async def wizard_start(ctx: Context) -> str:
    """开始一首新歌（或精修）。返回全部功能及每个功能要填的项，之后用 wizard_fill 一次填好。"""
    return await run(ctx, "wizard_start")


@mcp.tool()
async def wizard_fill(answers: dict[str, str], ctx: Context) -> str:
    """一次填多项，例如 {"feature": "text_song", "genre": "rnb", "mood": "sad", "language": "yue"}。
    值用选项的 value，也可以是自由文本、本机音频路径或下载链接、数字或歌词全文。
    返回已填/出错/忽略的项和真正还缺的下一项 next；全部填完时 next.done=true 并带 spec 和 defaults。"""
    return await run(ctx, "wizard_fill", answers=answers)


@mcp.tool()
async def wizard_answer(value: str, ctx: Context) -> str:
    """只回答当前这一项（等同于 wizard_fill 只填 next.step）。"""
    return await run(ctx, "wizard_answer", value=value)


@mcp.tool()
async def wizard_back(ctx: Context) -> str:
    """撤销上一个回答，回到上一题。"""
    return await run(ctx, "wizard_back")


@mcp.tool()
async def submit_song(ctx: Context, title: str = "", lyrics: str = "", style: str = "") -> str:
    """向导完成后提交生成任务。todo 含 write_lyrics 时 lyrics 必填。"""
    return await run(ctx, "submit_song", title=title or None, lyrics=lyrics or None, style=style or None)


@mcp.tool()
async def get_job(job_id: str, ctx: Context, wait_seconds: int = 0) -> str:
    """查询任务状态、进度、生成的音频路径、扒谱得到的 phrases（每句音符数）。wait_seconds 最多 50。"""
    return await run(ctx, "get_job", job_id=job_id, wait_seconds=wait_seconds)


@mcp.tool()
async def list_jobs(ctx: Context) -> str:
    """列出所有作品及状态。"""
    return await run(ctx, "list_jobs")


@mcp.tool()
async def provide_lyrics(job_id: str, lyrics: str, ctx: Context) -> str:
    """给状态为 needs_lyrics 的任务补上歌词并继续生成。"""
    return await run(ctx, "provide_lyrics", job_id=job_id, lyrics=lyrics)


@mcp.tool()
async def cancel_job(job_id: str, ctx: Context) -> str:
    """取消排队或运行中的任务。"""
    return await run(ctx, "cancel_job", job_id=job_id)


@mcp.tool()
async def style_reference(section: str, ctx: Context, keyword: str = "") -> str:
    """查风格描述参考。section: rules=写法要点和段落标签；presets=全部预设及 value；official=官方演示的风格描述；
    covers=官方改编演示。keyword 可选，只看含这个词的条目（如 jazz、古风、女声）。自己写 style 前先查。"""
    return await run(ctx, "style_reference", section=section, keyword=keyword or None)


def http_app():
    """ASGI app for mounting in the desktop server (path /mcp inside the mount)."""
    return mcp.streamable_http_app()


def main():
    global STDIO
    STDIO = True
    mcp.run()
