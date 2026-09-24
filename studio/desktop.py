"""Desktop entry point: embedded API server + native window (Edge WebView2). Built into YuEStudio.exe."""
from __future__ import annotations

import os
import sys
import threading
import time

from . import config


def _redirect_output():
    # A windowed exe has no console; uvicorn and print() need somewhere to write.
    if sys.stdout is None or sys.stderr is None:
        config.DATA.mkdir(parents=True, exist_ok=True)
        log = open(config.DATA / "app.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or log
        sys.stderr = sys.stderr or log


def _running():
    from . import agent
    try:
        agent.http("GET", "/api/system", timeout=2)
        return True
    except agent.ApiError:
        return False


class JsApi:
    """Functions the page can call as window.pywebview.api.* (desktop-only extras)."""

    def open_folder(self, job_id, rel=""):
        target = (config.DATA / "jobs" / job_id / rel).resolve()
        if not str(target).startswith(str((config.DATA / "jobs").resolve())):
            return False
        if target.is_file():
            os.system(f'explorer /select,"{target}"')
        else:
            os.startfile(target if target.exists() else config.DATA / "jobs")
        return True

    def open_install_folder(self):
        os.startfile(config.ROOT)
        return True


def main():
    _redirect_output()
    import webview

    if not _running():
        import uvicorn
        from .server import app
        server = uvicorn.Server(uvicorn.Config(app, host=config.HOST, port=config.PORT, log_config=None, log_level="warning"))
        threading.Thread(target=server.run, daemon=True).start()
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.1)
        if not server.started:
            webview.create_window("YuE Studio", html=f"<h3>端口 {config.PORT} 被占用，无法启动。</h3>")
            webview.start()
            return
    webview.create_window("YuE Studio", config.URL, width=1440, height=920, min_size=(1000, 680), js_api=JsApi())
    webview.start(private_mode=False, storage_path=str(config.DATA / "webview"))


if __name__ == "__main__":
    main()
