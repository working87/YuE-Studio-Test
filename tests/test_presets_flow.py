"""Expanded presets through the wizard: paging, pinned-first, more-options, free text, optional extra step."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import flow  # noqa: E402

fails = 0


def check(name, ok, detail=""):
    global fails
    fails += not ok
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail and not ok else ""))


def walk(answers):
    s = flow.new_state(agent=True)
    for v in answers:
        s = flow.answer(s, v)
    return s, flow.question(s)


s, q = walk(["text", "text_song"])
while q["step"] != "genre":  # steps before genre (lyrics source, theme...)
    s = flow.answer(s, q["options"][0]["value"] if q.get("options") else "夏天的海边")
    q = flow.question(s)
check("first genre question is genre", q["step"] == "genre", q.get("step"))
vals = [o["value"] for o in q["options"]]
pinned = [o["value"] for o in flow.FLOW["steps"]["genre"]["options"] if o.get("pin")]
check("page 1 shows pinned genres first", vals[0] in pinned, str(vals))
check("page has a more option", "__more__" in vals, str(vals))

# page through everything: every genre must be reachable
seen, st = set(), s
for _ in range(40):
    qq = flow.question(st)
    if qq["step"] != "genre":
        break
    seen |= {o["value"] for o in qq["options"] if o["value"] != "__more__"}
    if "__more__" not in [o["value"] for o in qq["options"]]:
        break
    st = flow.answer(st, "__more__")
allg = {o["value"] for o in flow.FLOW["steps"]["genre"]["options"]}
check("all 61 genres reachable by paging", allg <= seen, str(sorted(allg - seen))[:200])

# pick a non-pinned genre directly by value and by label
np = next(o for o in flow.FLOW["steps"]["genre"]["options"] if not o.get("pin"))
s2 = flow.answer(s, np["value"])
check("non-pinned value accepted directly", flow.question(s2)["step"] != "genre")
s3 = flow.answer(s, np["label"])
check("label accepted", flow.question(s3)["step"] != "genre")
s4 = flow.answer(s, "dreamy shoegaze, washed-out guitars")
check("free text genre accepted", flow.question(s4)["step"] != "genre")

# run a full text_song with extra="无" and with a real extra
def finish(extra):
    st = flow.new_state(agent=True)
    for v in ["text", "text_song"]:
        st = flow.answer(st, v)
    st, *_ = flow.fill(st, {"extra": extra})  # not asked any more; an agent fills it when the user mentions details
    for _ in range(30):
        qq = flow.question(st)
        if qq.get("done"):
            return qq
        step = qq["step"]
        if step == "extra":
            v = extra
        elif qq.get("options"):
            v = next(o["value"] for o in qq["options"] if o["value"] != "__more__")
        elif step == "theme":
            v = "夏天的海边"
        else:
            v = "1"
        st = flow.answer(st, v)
    raise AssertionError("wizard did not finish")


d1 = finish("无")
d2 = finish("intro only piano, strings join in chorus")
check("extra 无 not in style", "无" not in d1["spec"]["style"], d1["spec"]["style"])
check("extra text appended", "strings join in chorus" in d2["spec"]["style"], d2["spec"]["style"])
check("extra not asked by default", all(flow.question(flow.answer(flow.answer(flow.new_state(True), "text"), "text_song"))
                                         .get("step") != "extra" for _ in [0]))
print("FAILED" if fails else "ALL PASS", fails)
sys.exit(1 if fails else 0)
