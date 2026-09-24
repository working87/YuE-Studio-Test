"""Translation plumbing against a fake OpenAI-compatible endpoint (no real model/key needed)."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import agent, flow  # noqa: E402

seen = {}


class Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        seen.update(body=body, auth=self.headers["Authorization"])
        text = "```\n[Verse]\n朝の光が窓に落ちて\nコーヒーの香りが広がる\n\n[Chorus]\n今日もちゃんと愛していこう\n悩みはドアの外に置いて\n```"
        out = json.dumps({"choices": [{"message": {"role": "assistant", "content": text}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


server = HTTPServer(("127.0.0.1", 7998), Fake)
threading.Thread(target=server.serve_forever, daemon=True).start()
zh = "[Verse]\n清晨的光落在窗台\n咖啡的香慢慢散开\n\n[Chorus]\n今天也要好好地爱\n把烦恼都留在门外"
out = agent.translate_lyrics({"base_url": "http://127.0.0.1:7998", "model": "m", "api_key": "k"}, zh, "ja")
assert "tools" not in seen["body"], "translation must not send tools"
assert seen["auth"] == "Bearer k"
assert "日本語" in seen["body"]["messages"][1]["content"]
assert not out.startswith("```") and out.count("\n") == zh.count("\n"), out
assert flow.detect_language(out) == "ja"
print("translate plumbing OK:", out.replace("\n", " / "))
