"""style_reference tool: every section non-empty, keyword filtering keeps headings, both agents expose it."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import agent  # noqa: E402

fails = 0


def check(name, ok, detail=""):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail and not ok else ""))


for sec in agent.GUIDE_SECTIONS:
    text = agent.style_reference(sec)
    check(f"section {sec} non-empty", len(text) > 200, text[:80])
jazz = agent.style_reference("presets", "jazz")
check("presets jazz has genre row", "`jazz`" in jazz.lower() or "jazz" in jazz.lower(), jazz[:200])
check("presets jazz keeps table header", "| value" in jazz)
check("presets jazz excludes unrelated rows", "`pop`" not in jazz)
off = agent.style_reference("official", "Enka")
check("official keyword heading", "### Enka" in off, off[:200])
check("missing keyword message", "没有含" in agent.style_reference("rules", "zzzz"))
s = agent.Session()
r = s.call("style_reference", {"section": "bad"})
check("bad section -> error", "error" in r)
check("tool in openai schema", any(t["function"]["name"] == "style_reference" for t in agent.openai_tools()))
from studio import mcp_server  # noqa: E402
import anyio  # noqa: E402
names = [t.name for t in anyio.run(mcp_server.mcp.list_tools)]
check("tool in MCP", "style_reference" in names, str(names))
print("FAILED" if fails else "ALL PASS", fails)
sys.exit(1 if fails else 0)
