"""Static audit: for every feature × step × option, what does the answer change in the job spec?

An option that changes nothing, or only changes the style text while the pipeline would need
something else (e.g. language vs. the lyrics actually written), is reported.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from studio import flow  # noqa: E402

SAMPLE = {"file": "uploads/x.wav", "text": "主题", "lyrics": "[Verse]\n你好", "number": 90, "job": "J1",
          "abc": "X:1\nK:C\nV: Vocal\nC4|\nV: Ins\nZ|"}


def first_answers(feature, agent):
    """Walk the wizard answering each question with its first option / a sample value."""
    s = flow.new_state(agent)
    s = flow.answer(s, flow.FLOW["features"][feature]["category"])
    s = flow.answer(s, feature)
    path = []
    while not (q := flow.question(s))["done"]:
        step = q["step"]
        value = q["all_options"][0]["value"] if q["type"] == "choice" else SAMPLE[q["type"]]
        path.append(step)
        s = flow.answer(s, value)
    return s, path


def spec_of(state):
    spec = flow.build_spec(state)
    spec.pop("seed")
    return spec


problems = 0
for agent in (False, True):
    for feature in flow.FLOW["features"]:
        base_state, path = first_answers(feature, agent)
        base = spec_of(base_state)
        for step in path:
            info = flow.step_def(step)
            if info["type"] != "choice":
                continue
            opts = flow.options(step, base_state["answers"], agent)
            specs = {}
            for opt in opts:
                st = copy.deepcopy(base_state)
                st["answers"][step] = opt["value"]
                if flow.pending(st):
                    continue  # changes which later steps apply; covered by its own walk
                specs[opt["value"]] = json.dumps(spec_of(st), sort_keys=True, ensure_ascii=False)
            if len(specs) > 1 and len(set(specs.values())) == 1:
                problems += 1
                print(f"[DEAD] {'agent' if agent else 'web'} {feature}.{step}: options {list(specs)} all give the same spec")
        if not agent:
            print(f"web {feature:18} steps: {' → '.join(path)}")
print(f"\n{problems} dead option groups")
