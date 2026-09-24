"""Small text edits on the two-voice (Vocal/Ins) ABC dialect used by YuE2 and SheetSage2.

Validation stays with the official abc_tools.py; these helpers only do the
edits the studio needs and are checked by it afterwards.
"""
from __future__ import annotations

import re

VOICE_LINE = re.compile(r"^V:\s*(Vocal|Ins)\s*$")
NOTE = re.compile(r'"[^"\n]*"|\[K:[^\]\n]+\]|(?P<acc>\^\^|__|\^|_|=)?(?P<note>[A-Ga-gzZ])[,\']*\d*(?P<tie>-?)')


def split(abc):
    """Return (header_lines, body_lines); the header ends with the first K: line."""
    lines = abc.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("K:"):
            return lines[:i + 1], lines[i + 1:]
    raise ValueError("ABC has no K: line")


def set_tempo(abc, bpm):
    header, body = split(abc)
    header = [l for l in header if not l.startswith("Q:")]
    at = next((i + 1 for i, l in enumerate(header) if l.startswith("L:")), len(header) - 1)
    header.insert(at, f"Q:1/4={int(bpm)}")
    return "\n".join(header + body) + "\n"


def tempo(abc):
    m = re.search(r"^Q:\s*1/4\s*=\s*(\d+)", abc, re.M)
    return int(m.group(1)) if m else None


def _blocks(body):
    """[(voice or None, lines)] in order; comment/section lines stay in a None block."""
    blocks, current = [], [None, []]
    for line in body:
        m = VOICE_LINE.match(line.strip())
        if m:
            blocks.append(current)
            current = [m.group(1), []]
        elif line.strip().startswith("%") and current[0] is not None:
            blocks.append(current)
            current = [None, [line]]
        else:
            current[1].append(line)
    blocks.append(current)
    return blocks


def swap_voices(abc):
    """Exchange the Vocal and Ins parts block by block (same time grid, so bars stay aligned)."""
    header, body = split(abc)
    blocks = _blocks(body)
    vocal = [b for b in blocks if b[0] == "Vocal"]
    ins = [b for b in blocks if b[0] == "Ins"]
    if len(vocal) != len(ins):
        raise ValueError("Expected paired Vocal/Ins blocks")
    for v, i in zip(vocal, ins):
        v[1], i[1] = i[1], v[1]
    out = list(header)
    for voice, lines in blocks:
        if voice:
            out.append(f"V: {voice}")
        out.extend(lines)
    return "\n".join(out).rstrip("\n") + "\n"


def _bar_counts(lines):
    bars = []
    for bar in "".join(lines).split("|"):
        if not bar.strip():
            continue
        count, tied = 0, False
        for m in NOTE.finditer(bar):
            if not m.group("note"):
                continue
            if m.group("note") not in "zZ" and not tied:
                count += 1
            tied = bool(m.group("tie"))
        bars.append(count)
    return bars


def voice_notes(abc, voice):
    _, body = split(abc)
    return sum(sum(_bar_counts(lines)) for kind, lines in _blocks(body) if kind == voice)


def phrase_report(abc, voice="Vocal"):
    """Sections → phrases (one voice block ≈ one lyric line) with note counts, for fitting lyrics."""
    _, body = split(abc)
    sections, name = [], "song"
    for kind, lines in _blocks(body):
        if kind is None:
            for line in lines:
                if line.strip().startswith("%"):
                    name = line.strip().lstrip("% ").strip() or name
            continue
        if kind != voice:
            continue
        bars = _bar_counts(lines)
        if not sum(bars):
            continue  # instrumental gap: no lyric line
        if not sections or sections[-1]["section"] != name:
            sections.append({"section": name, "lines": []})
        sections[-1]["lines"].append({"notes": sum(bars), "notes_per_bar": bars})
    for s in sections:
        s["notes"] = sum(line["notes"] for line in s["lines"])
    return {"voice": voice, "bpm": tempo(abc), "sections": sections,
            "total_notes": sum(s["notes"] for s in sections),
            "hint": "每个 section 写一段，lines 里每一项写一句歌词；中文约一字一音（字数≈notes），"
                    "英文按音节数对齐，重音落在强拍。"}


# ---------- plan post-processing (length, instrumental) ----------
MULTI_REST = re.compile(r"^\s*Z(\d*)\s*$")
TO_REST = re.compile(r'"[^"\n]*"|\[K:[^\]\n]+\]|(?:\^\^|__|\^|_|=)?[A-Ga-g][,\']*(\d*)-?')
CHORD = re.compile(r'"[^"\n]*"')


def _bars(lines):
    """Bars in one voice block; 'Z3' spans three bars."""
    count = 0
    for seg in "".join(lines).split("|"):
        if seg.strip():
            m = MULTI_REST.match(seg)
            count += int(m.group(1) or 1) if m else 1
    return count


def beats_per_bar(abc):
    m = re.search(r"^M:\s*(\d+)/(\d+)", abc, re.M)
    return int(m.group(1)) * 4 / int(m.group(2)) if m else 4.0


def _units(body):
    """Phrase units: leading comments + one Vocal block + one Ins block, with section name and bar count."""
    units, pending, name = [], [], "song"
    for kind, lines in _blocks(body):
        if kind is None:
            for line in lines:
                if line.strip().startswith("%"):
                    name = line.strip().lstrip("% ").strip() or name
            pending.extend(lines)
        elif kind == "Vocal" or not units or units[-1]["closed"]:
            units.append({"section": name, "pre": pending, "Vocal": [], "Ins": [], "closed": False})
            pending = []
            units[-1][kind] = lines
        else:
            units[-1][kind] = lines
            units[-1]["closed"] = True
    for u in units:
        u["bars"] = max(_bars(u["Vocal"]), _bars(u["Ins"]))
    return units, pending


def _join(header, units, tail):
    out = list(header)
    for u in units:
        out += u["pre"] + ["V: Vocal"] + u["Vocal"] + ["V: Ins"] + u["Ins"]
    return "\n".join(out + tail).rstrip("\n") + "\n"


def duration_seconds(abc):
    _, body = split(abc)
    units, _ = _units(body)
    bpm = tempo(abc) or 100
    return sum(u["bars"] for u in units) * beats_per_bar(abc) * 60 / bpm


def trim_to_seconds(abc, seconds, tolerance=1.15):
    """Keep whole sections (then whole phrases) until the target length; returns the same ABC if already short."""
    header, body = split(abc)
    units, tail = _units(body)
    bar_seconds = beats_per_bar(abc) * 60 / (tempo(abc) or 100)
    limit = seconds * tolerance / bar_seconds
    if sum(u["bars"] for u in units) <= limit:
        return abc
    sections = []
    for u in units:
        if not sections or sections[-1][0]["section"] != u["section"]:
            sections.append([])
        sections[-1].append(u)
    # Keep the planned ending: a score cut mid-section makes the model keep playing past it.
    # A long outro keeps only its closing phrases (at most ~35% of the length).
    ending = []
    if len(sections) > 1 and re.search(r"outro|ending|coda|end", sections[-1][0]["section"], re.I):
        outro = sections.pop()
        for u in reversed(outro):
            if sum(e["bars"] for e in ending) + u["bars"] > 0.35 * limit and ending:
                break
            ending.insert(0, u)
        if sum(e["bars"] for e in ending) > 0.5 * limit:
            ending = []
        elif ending and ending[0] is not outro[0]:  # keep the "% outro" marker the model plans endings by
            ending[0] = {**ending[0], "pre": outro[0]["pre"] + ending[0]["pre"]}
        limit -= sum(e["bars"] for e in ending)
    kept, total = [], 0
    for sec in sections:
        bars = sum(u["bars"] for u in sec)
        if total + bars <= limit:
            kept += sec
            total += bars
            continue
        for u in sec:  # partial section: contiguous whole phrases only
            if total + u["bars"] > limit and kept:
                break
            kept.append(u)
            total += u["bars"]
        break
    kept[-1]["Vocal"], kept[-1]["Ins"] = _untie_end(kept[-1]["Vocal"]), _untie_end(kept[-1]["Ins"])  # nothing follows as planned
    kept += ending
    kept[-1]["Vocal"], kept[-1]["Ins"] = _untie_end(kept[-1]["Vocal"]), _untie_end(kept[-1]["Ins"])  # song ends here
    return _join(header, kept, [])


def _untie_end(lines):
    """Drop a tie on the last note of a block (nothing to tie into after it)."""
    lines = list(lines)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            lines[i] = re.sub(r"-(\s*\|?\s*)$", r"\1", lines[i].rstrip())
            break
    return lines


def _rests(lines):
    return [TO_REST.sub(lambda m: m.group(0) if m.group(0).startswith(('"', "[")) else "z" + m.group(1), l) for l in lines]


def instrumentalize(abc):
    """Silence the sung line; if the instrument part is resting there, it takes over the melody.

    Chord symbols stay in the Vocal voice (where the native dialect keeps harmony)."""
    header, body = split(abc)
    units, tail = _units(body)
    replaced = [False] * len(units)
    for i, u in enumerate(units):
        if not sum(_bar_counts(u["Vocal"])):
            continue
        if not sum(_bar_counts(u["Ins"])):
            u["Ins"] = [CHORD.sub("", l) for l in u["Vocal"]]
            replaced[i] = True
        u["Vocal"] = _rests(u["Vocal"])
    # A tie may not cross into material that was swapped in or out.
    for i, u in enumerate(units):
        if replaced[i] or (i + 1 < len(units) and replaced[i + 1]):
            u["Ins"] = _untie_end(u["Ins"])
    return _join(header, units, tail)


NOTE_OCTAVE = re.compile(r'"[^"\n]*"|\[K:[^\]\n]+\]|(?P<acc>\^\^|__|\^|_|=)?(?P<note>[A-Ga-g])(?P<oct>[,\']*)')


def _shift_octave(match, up):
    if not match.group("note"):
        return match.group(0)
    acc, note, octs = match.group("acc") or "", match.group("note"), match.group("oct")
    if up:
        if "," in octs:
            octs = octs[:-1]
        elif note.isupper():
            note = note.lower()
        else:
            octs += "'"
    else:
        if "'" in octs:
            octs = octs[:-1]
        elif note.islower():
            note = note.upper()
        else:
            octs += ","
    return acc + note + octs


def transpose_voice(abc, voice="Vocal", octaves=-1):
    """Move one voice by whole octaves (harmony unchanged); chords and rests are untouched."""
    header, body = split(abc)
    out, current = list(header), None
    for line in body:
        m = VOICE_LINE.match(line.strip())
        if m:
            current = m.group(1)
        elif current == voice and not line.strip().startswith("%"):
            for _ in range(abs(octaves)):
                line = NOTE_OCTAVE.sub(lambda mm: _shift_octave(mm, octaves > 0), line)
        out.append(line)
    return "\n".join(out).rstrip("\n") + "\n"