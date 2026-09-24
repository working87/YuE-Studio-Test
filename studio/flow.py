"""Question-by-question router shared by the agent skill, the CLI and the web UI.

State is a plain JSON dict so an agent can keep it in a file between turns:
    {"answers": {step_id: value}, "page": 0, "agent": true}
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

FLOW = json.loads((Path(__file__).with_name("flow.json")).read_text(encoding="utf-8"))
MORE, BACK = "__more__", "__back__"
TARGET_SECONDS = {"short": 60, "standard": 150, "long": 240}
HUM_INSTRUMENTAL_LYRICS = "[Instrumental Intro]\n\n[Instrumental Break]\n\n[Instrumental Outro]"


def lead_tag(lead):
    """English instrument name of a lead preset (free text is used as written)."""
    return next((o.get("tag") for o in FLOW["steps"]["lead"]["options"] if o["value"] == lead), lead)


def hum_instrumental_lyrics(lead):
    """Instrumental section tags that also name the lead, like the official demos' "[Intro: Piano & Flute]"."""
    tag = lead_tag(lead) if lead else None
    if not tag:
        return HUM_INSTRUMENTAL_LYRICS
    return f"[Instrumental Intro: {tag}]\n\n[Instrumental Break: {tag} Solo]\n\n[Instrumental Outro: {tag}]"


def _hum_instrumental_opening(a):
    """The lead instrument goes first: the model weighs the start of the style most."""
    tag = lead_tag(a.get("lead")) if a.get("lead") else None
    return f"{tag}-led instrumental, no vocals. " if tag else "Instrumental, no vocals. "


INSTRUMENTAL_LYRICS = {
    "short": "[Intro]\n\n[Theme]\n\n[Outro]",
    "standard": "[Intro]\n\n[Theme]\n\n[Development]\n\n[Theme]\n\n[Bridge]\n\n[Theme]\n\n[Outro]",
    "long": "[Intro]\n\n[Theme A]\n\n[Theme B]\n\n[Development]\n\n[Theme A]\n\n[Solo]\n\n[Theme B]\n\n[Outro]",
}


def new_state(agent=True):
    return {"answers": {}, "page": 0, "agent": agent}


def step_def(step):
    info = dict(FLOW["steps"][step])
    if "options_from" in info:  # same presets as another step, asked differently
        info["options"] = FLOW["steps"][info["options_from"]]["options"]
    if step in FLOW.get("step_when", {}):
        info["when"] = FLOW["step_when"][step]
    return info


def feature_steps(answers):
    steps = ["category"]
    if "category" in answers:
        steps.append("feature")
    feature = answers.get("feature")
    if feature:
        steps += FLOW["features"][feature]["steps"]
    return steps


def visible(step, answers, steps, agent):
    if not agent and "lyrics_source" in steps:
        # The web UI has no LLM, so lyrics are always typed by hand there.
        if step in ("lyrics_source", "theme", "structure"):
            return False
        if step == "lyrics":
            return True
    cond = step_def(step).get("when")
    if cond:
        relevant = {k: v for k, v in cond.items() if k in steps}
        if relevant and not any(answers.get(k) in allowed for k, allowed in relevant.items()):
            return False
    return True


def options(step, answers, agent):
    feature = answers.get("feature")
    if step == "category":
        return FLOW["categories"]
    if step == "feature":
        return [{"value": k, "label": f["label"], "desc": f["desc"]}
                for k, f in FLOW["features"].items() if f["category"] == answers.get("category")]
    result = []
    for opt in step_def(step).get("options", []):
        if "only" in opt and feature not in opt["only"]:
            continue
        if opt.get("agent_only") and not agent:
            continue
        if step == "language" and opt["value"] == "auto" and agent and answers.get("lyrics_source") != "self":
            continue  # the agent writes the lyrics, so it must be told which language to write
        result.append(opt)
    return result


def pending(state):
    answers, agent = state["answers"], state.get("agent", True)
    steps = feature_steps(answers)
    todo = [s for s in steps if s not in answers and visible(s, answers, steps, agent)]
    if not agent and lyrics_optional(answers):
        todo = [s for s in todo if s != "lyrics"]  # empty → job pauses after transcription for lyrics
    if not agent:
        todo = [s for s in todo if not step_def(s).get("optional")]  # the form shows them; leaving them empty is fine
    else:
        todo = [s for s in todo if not step_def(s).get("agent_skip")  # defaults unless the user brings them up
                and not (s == "language" and _auto_language(answers, agent))]
    return todo


def _auto_language(answers, agent):
    """The user supplies the lyrics, so the sung language is read off them; nothing to ask."""
    return any(o["value"] == "auto" for o in options("language", answers, agent))


def defaults(state):
    """What an agent run uses for the steps it does not ask (shown in the confirmation summary)."""
    a = state["answers"]
    steps = feature_steps(a)
    out = {}
    if "variants" in steps and "variants" not in a:
        out["variants"] = f"{default_variants(a.get('feature'))} 个版本"
    if "tempo" in steps and "tempo" not in a:
        out["tempo"] = "跟随原曲/哼唱" if FLOW["features"][a["feature"]]["pipeline"].get("transcribe") else "由模型决定"
    if "language" in steps and "language" not in a and _auto_language(a, True):
        out["language"] = "跟随歌词自动识别"
    if "plan_mode" in steps and "plan_mode" not in a:
        out["plan_mode"] = "完整规划（先出乐谱再出歌）"
    return out


def default_variants(feature):
    # 哼唱 → 纯音乐 still hums along in about half the takes, and a take is short: offer four to choose from.
    return 4 if feature == "hum_instrumental" else 1


def lyrics_optional(answers):
    feature = answers.get("feature")
    return bool(feature and FLOW["features"][feature]["pipeline"].get("transcribe"))


def question(state, page_size=4):
    """Next question. page_size=4 paginates for tools that cap options at 4; None returns every option at once."""
    todo = pending(state)
    if not todo:
        return {"done": True, "spec": build_spec(state)}
    step = todo[0]
    info = step_def(step)
    q = {"done": False, "step": step, "type": info["type"], "question": info["q"],
         "progress": f"{len(state['answers']) + 1}/{len(state['answers']) + len(todo)}",
         "can_go_back": bool(state["answers"])}
    for key in ("accept", "min", "max"):
        if key in info:
            q[key] = info[key]
    if info.get("optional"):
        q["optional"] = True
        q["question"] += "（回答“无”跳过）"
    if info["type"] == "choice":
        raw = options(step, state["answers"], state.get("agent", True))
        raw = [o for o in raw if o.get("pin")] + [o for o in raw if not o.get("pin")]  # common choices first
        opts = [{k: o[k] for k in ("value", "label", "desc") if k in o} for o in raw]
        q["custom_allowed"] = bool(info.get("custom"))
        if page_size is None:  # chat agents: the whole list, compact, grouped
            q["options"] = [{"value": o["value"], "label": o["label"], **({"group": o["group"]} if o.get("group") else {}),
                             **({"desc": o["desc"]} if o.get("desc") and len(raw) <= 12 else {})} for o in raw]
            return q
        if any(o.get("group") for o in raw):  # long lists: an overview so an agent can list them compactly
            groups = {}
            for o in raw:
                groups.setdefault(o.get("group", "其他"), []).append(o["label"])
            q["groups"] = groups
        per = page_size - 1 if len(opts) > page_size else page_size
        pages = [opts[i:i + per] for i in range(0, len(opts), per)]
        page = state.get("page", 0) % max(len(pages), 1)
        q["options"] = pages[page] + ([{"value": MORE, "label": "更多选项…", "desc": f"第 {page + 1}/{len(pages)} 页"}] if len(pages) > 1 else [])
        q["all_options"] = opts
    return q


def answer(state, value):
    """Apply one answer. Choice steps accept an option value or free text when custom is allowed."""
    state = json.loads(json.dumps(state))
    if value == BACK:
        if state["answers"]:
            last = list(state["answers"])[-1]
            state["answers"].pop(last)
            if last == "category":
                state["answers"].pop("feature", None)
        state["page"] = 0
        return state
    if value == MORE:
        state["page"] = state.get("page", 0) + 1
        return state
    todo = pending(state)
    if not todo:
        raise ValueError("Flow already complete")
    return _set(state, todo[0], value)


def fill(state, values):
    """Apply several answers at once (an agent read them off one user message), in flow order.

    Returns (state, filled steps, errors {step: message}, ignored steps). `feature` implies its category;
    steps the chosen feature does not have (or has not reached yet because of a missing earlier answer) are ignored.
    """
    state = json.loads(json.dumps(state))
    values = {k: v for k, v in dict(values).items() if v is not None and str(v).strip() != ""}
    if "feature" in values and values["feature"] in FLOW["features"] and "category" not in values:
        values["category"] = FLOW["features"][values["feature"]]["category"]
    filled, errors = [], {}
    progress = True
    while progress:
        progress = False
        steps = feature_steps(state["answers"])
        for step in [s for s in steps if s not in state["answers"] and visible(s, state["answers"], steps, state.get("agent", True))]:
            if step in values and step not in errors:
                try:
                    state = _set(state, step, values[step])
                    filled.append(step)
                except ValueError as exc:
                    errors[step] = str(exc)
                progress = True
                break  # answering can change which steps exist (category → feature → its steps)
    ignored = [k for k in values if k not in filled and k not in errors]
    return state, filled, errors, ignored


def _set(state, step, value):
    state = json.loads(json.dumps(state))
    info = step_def(step)
    if info["type"] == "choice":
        opts = options(step, state["answers"], state.get("agent", True))
        valid = {o["value"] for o in opts}
        # Chat models often echo the label the user clicked; map it back to the option value.
        norm = str(value).strip().lower()
        value = next((o["value"] for o in opts if norm in (o["value"].lower(), o["label"].lower())), value)
        if value not in valid and not (info.get("custom") and isinstance(value, str) and value.strip()):
            raise ValueError(f"{step}: '{value}' is not one of {sorted(valid)}")
        if step == "category":
            state["answers"].pop("feature", None)
    elif info["type"] == "number":
        value = int(value)
        if not info.get("min", -10**9) <= value <= info.get("max", 10**9):
            raise ValueError(f"{step}: {value} out of range")
    elif not str(value).strip():
        raise ValueError(f"{step}: empty answer")
    state["answers"][step] = value
    state["page"] = 0
    return state


LANG_NAMES = {"zh": "中文", "yue": "粤语", "en": "英语", "ja": "日语", "ko": "韩语"}
SCRIPT = {"zh": "han", "yue": "han", "en": "latin", "ja": "ja", "ko": "ko"}
STYLE_LANGUAGES = {"Mandarin": "zh", "Cantonese": "yue", "English": "en", "Japanese": "ja", "Korean": "ko"}


SRT_NOISE = re.compile(r"^\s*(\d+|\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}|\[\d{1,2}:\d{2}(?:[.:]\d{1,3})?\].*)\s*$")
LRC_TIME = re.compile(r"^\s*(?:\[\d{1,2}:\d{2}(?:[.:]\d{1,3})?\])+")


def normalize_lyrics(text):
    """Accept pasted subtitles as-is: drop SRT numbers/timecodes and LRC time tags, and add a [Verse]
    tag when the lyrics carry no section tags (YuE2 expects at least one)."""
    if not text or not text.strip():
        return text
    lines = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = LRC_TIME.sub("", raw).strip()
        if raw.strip() and not line:
            continue  # an LRC line that held only a time tag
        if SRT_NOISE.match(raw) and not LRC_TIME.match(raw):
            continue
        lines.append(line)
    body = "\n".join(lines).strip()
    body = re.sub(r"\n{3,}", "\n\n", body)
    if not re.search(r"^\[[^\]]+\]\s*$", body, re.M):
        body = "[Verse]\n" + "\n".join(l for l in body.split("\n") if l.strip())
    return body


def detect_language(lyrics):
    """zh / ja / ko / en from the writing system of the lyrics (section tags ignored); None if no text."""
    if not lyrics:
        return None
    text = re.sub(r"\[[^\]]*\]", "", lyrics)
    hangul = len(re.findall(r"[가-힯ᄀ-ᇿ]", text))
    kana = len(re.findall(r"[぀-ヿ]", text))
    han = len(re.findall(r"[一-鿿]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    total = hangul + kana + han + latin
    if not total:
        return None
    if hangul > 0.2 * total:
        return "ko"
    if kana > 0.05 * total:
        return "ja"
    return "zh" if han >= latin / 3 else "en"


def vocal_register(vocal):
    """'male' / 'female' for a single chosen (or typed) singer; the runner keeps the planned line in that range."""
    if not vocal:
        return None
    text = (_style_fragment("vocal", vocal) or "").lower()
    if re.search(r"duet|对唱|choir|合唱", text):
        return None
    if re.search(r"female|女", text):
        return "female"
    # Male voices are left in the register the model planned: the automatic octave-down (sung ~115–147 Hz)
    # sounded too low to the user, so it is disabled. Re-enable by returning "male" here.
    return None


def mismatch_message(chosen, found):
    return (f"歌词是{LANG_NAMES[found]}，但选择了用{LANG_NAMES[chosen]}唱。模型唱的就是歌词本身，"
            f"请改成「跟随歌词」，或者把歌词换成{LANG_NAMES[chosen]}（可以用 AI 翻译）。")


def fit_language(style, lyrics):
    """Make the style's language tag match the lyrics (used when lyrics arrive after the wizard)."""
    found = detect_language(lyrics)
    if not found:
        return style
    tags = [t.strip() for t in (style or "").split(",") if t.strip()]
    tagged = [t for t in tags if t in STYLE_LANGUAGES]
    if tagged and SCRIPT[STYLE_LANGUAGES[tagged[0]]] != SCRIPT[found]:
        raise ValueError(mismatch_message(STYLE_LANGUAGES[tagged[0]], found))
    if not tagged:
        tags.insert(0, _style_fragment("language", found))
    return ", ".join(tags)


def _style_fragment(step, value):
    for opt in step_def(step).get("options", []):
        if opt["value"] == value:
            return opt.get("style")
    return value  # custom free text is used verbatim


def build_spec(state):
    """Turn answers into a job spec understood by studio.pipeline."""
    answers, agent = state["answers"], state.get("agent", True)
    steps = feature_steps(answers)
    # Only answers to steps that currently apply: switching e.g. "用原歌词" to "换新歌词" in the form hides the
    # pasted lyrics, and a hidden answer must not leak into the song.
    a = {k: v for k, v in answers.items()
         if k not in steps or k in ("category", "feature") or visible(k, answers, steps, agent)}
    feature = a["feature"]
    meta = FLOW["features"][feature]
    pipe = dict(meta["pipeline"])
    if feature == "cover" and a.get("style_mode") == "new" and a.get("harmony", "reharm") == "reharm":
        # A new style with new harmony: keep only the sung melody and let the model re-harmonise it
        # (otherwise the original chords come along and hold the arrangement close to the original).
        pipe = {"transcribe": "melody-full", "target_voice": "Vocal", "cot": "melody"}
    instrumental = pipe.get("instrumental", False)
    lyrics = normalize_lyrics(a.get("lyrics") or a.get("orig_lyrics"))
    parts = []
    # What is sung is the lyrics themselves, so the language tag must describe the lyrics.
    chosen = a.get("language")
    language = detect_language(lyrics) if chosen in (None, "auto") else chosen
    mismatch = None
    if chosen not in (None, "auto") and lyrics:
        found = detect_language(lyrics)
        if found and SCRIPT[found] != SCRIPT[chosen]:
            mismatch = {"chosen": chosen, "lyrics": found}
    if not instrumental and language:
        parts.append(_style_fragment("language", language))
    genre_step = "genre" if a.get("genre") else "orig_genre"
    for step in (genre_step, "mood", "vocal", "hum_singer", "lead"):
        if a.get(step) and not (instrumental and step == "vocal"):
            fragment = _style_fragment(step, a[step])
            if step == "genre" and a.get("lead"):  # a chosen lead instrument replaces the genre's default ones
                fragment = next((o.get("core", fragment) for o in FLOW["steps"]["genre"]["options"]
                                 if o["value"] == a["genre"]), fragment)
            parts.append(fragment)
    hum_instrumental = instrumental and bool(a.get("hum_audio"))
    if hum_instrumental:
        # With a hummed melody the model tends to hum along; saying it at both ends plus instrumental section
        # tags doubled the clean takes. Without a hum it did not help, so plain instrumentals keep the
        # short wording (docs/EXPERIMENTS.md).
        parts.append("purely instrumental, no singing, no humming")
    elif instrumental:
        parts.append("instrumental, no vocals")
    extra = str(a.get("extra") or "").strip()
    if extra and extra.lower() not in ("无", "跳过", "没有", "不用", "none", "skip", "no"):
        parts.append(extra)  # free-form arrangement notes, like the official demo prompts
    tempo = a.get("tempo")
    bpm = None
    if tempo and tempo != "follow":
        bpm = int(tempo)
        parts.append(f"{bpm} BPM")
    if a.get("new_tempo"):
        bpm = int(a["new_tempo"])
    spec = {
        "feature": feature, "label": meta["label"],
        "style": ((_hum_instrumental_opening(a) if hum_instrumental else "") + ", ".join(p for p in parts if p)) or None,
        "lyrics": lyrics,
        "cot": a.get("plan_mode", pipe.get("cot", "full")),
        "transcribe": pipe.get("transcribe"),
        "keep_voice": pipe.get("keep_voice"),
        "target_voice": pipe.get("target_voice"),
        "audio": a.get("hum_audio") or a.get("ref_audio"),
        "bpm": bpm,
        "base_job": a.get("base_job"),
        "edit_type": a.get("edit_type"),
        "abc": a.get("abc"),
        "variants": int(a.get("variants", default_variants(feature))),
        "seed": random.randrange(1, 2**31),
        "vram": a.get("vram", "auto"),
        "language": language,
        "vocal_register": vocal_register(a.get("vocal") or a.get("hum_singer")),
        "language_mismatch": mismatch,
        "todo": [],
    }
    spec["instrumental"] = instrumental
    if instrumental and not spec["lyrics"]:
        # With a hum the melody sets the form; only three sections, all marked instrumental like the official demos.
        spec["lyrics"] = (hum_instrumental_lyrics(a.get("lead")) if spec["audio"]
                          else INSTRUMENTAL_LYRICS[a.get("structure", "standard")])
    if instrumental and not spec["audio"]:
        # YuE2 has no length parameter: the planned score is trimmed to this length before audio.
        spec["target_seconds"] = TARGET_SECONDS[a.get("structure", "standard")]
    if feature == "remix":
        spec["cot"] = "full"  # keep the retained score, harmony included
    if a.get("lyrics_source") == "agent":
        spec["theme"] = a.get("theme")
        spec["structure"] = a.get("structure")
        # Melody-conditioned jobs pause after transcription so lyrics can follow the note counts.
        spec["todo"].append("write_lyrics_after_transcription" if spec["transcribe"] else "write_lyrics")
    return spec
