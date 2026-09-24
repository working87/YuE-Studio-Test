"""Regenerate studio/style_guide.md: the style-writing reference the agents read.

Built from the official YuE2 demo page data (cases.js, lyrics are NOT copied) and studio/flow.json.
    .venv\\Scripts\\python.exe scripts\\build_style_guide.py [path\\to\\yue2demo]
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "AppData/Local/Temp/yue2demo")
OUT = ROOT / "studio/style_guide.md"

text = (DEMO / "cases.js").read_text(encoding="utf-8")
data = json.loads(text[text.index("{"):text.rindex("}") + 1])
cases, covers = data["cases"], data.get("covers", [])
flow = json.loads((ROOT / "studio/flow.json").read_text(encoding="utf-8"))
steps = flow["steps"]

tag_heads, detailed = collections.Counter(), collections.Counter()
for c in cases:
    for t in re.findall(r"\[([^\]\n]+)\]", c.get("lyrics") or ""):
        head, _, rest = t.partition(":")
        tag_heads[head.strip()] += 1
        if rest.strip():
            detailed[t.strip()] += 1
lens = sorted(len(c.get("tags") or "") for c in cases)
langs = collections.Counter(c.get("languageLabel") for c in cases)

L = []
w = L.append
w("# YuE2 风格描述参考（给 agent 读）\n")
w("本文件由 `scripts/build_style_guide.py` 从官方演示页数据和 `studio/flow.json` 生成。"
  "用于：帮用户把一句口语需求写成好的 style（风格描述），或在预设之外自由发挥。\n")
w("## 1. 模型怎么读风格描述\n")
w(f"- 官方演示共 {len(cases)} 首（全部带人声），{len({c['genre'] for c in cases})} 种曲风；"
  f"语言：{', '.join(f'{k} {v}' for k, v in langs.most_common())}。")
w(f"- 风格描述长度：中位数 {lens[len(lens) // 2]} 字符，最短 {lens[0]}，最长 {lens[-1]}。"
  "两种写法都有效：逗号分隔的标签（`funk, upbeat, male vocal`），或一段完整的编曲描述（从前奏写到尾奏）。")
w("- 推荐顺序：曲风 → 核心乐器 → 情绪 → 人声（性别/音色/唱法）→ 速度/节奏感 → 制作质感。"
  "本软件会自动把语言（Mandarin/Cantonese/English...）加在最前面，不用自己写。")
w("- 实测：模型强烈跟随“唱的那条旋律”，伴奏（Ins 声部）只弱跟随。"
  "所以“某乐器演奏主旋律”这类描述只能影响音色和编曲，不能保证乐器逐音复现哼唱。")
w("- 不要在 style 里写真实歌手名字冒充原唱；描述音色和唱法即可（例如 breathy airy female vocal）。")
w("- 歌词里的段落标签可以带乐器注释，官方就这么写，例如 `[Intro: Piano & Flute]`、`[Guitar Solo]`；"
  "纯器乐段用 `[Instrumental Break]`、`[Interlude]`，段内不写歌词。\n")
w("## 2. 段落标签（官方演示统计）\n")
w("| 标签 | 次数 |\n|---|---|")
for k, v in tag_heads.most_common(30):
    w(f"| `[{k}]` | {v} |")
w("\n带乐器/演唱注释的标签示例：" + "、".join(f"`[{k}]`" for k, _ in detailed.most_common(25)) + "\n")

w("## 3. 本软件的预设（向导选项）\n")
w("向导的 value 必须用下表的 value；表外的想法可以直接写英文描述作为自由文本（custom_allowed 为真时）。"
  "`core` 是有旋律输入时（哼唱/参考歌曲）用的精简版，避免乐器描述把旋律带跑。\n")
for sid, title in (("genre", "曲风"), ("mood", "情绪"), ("vocal", "人声"), ("lead", "主奏乐器（纯音乐）"),
                   ("tempo", "速度"), ("language", "语言")):
    opts = steps[sid]["options"]
    w(f"### {title} `{sid}`（{len(opts)} 项，★=界面常用）\n")
    w("| value | 名称 | 分组 | style 片段 |\n|---|---|---|---|")
    for o in opts:
        frag = o.get("style") or (f"{o['bpm']} BPM" if o.get("bpm") else o.get("desc", ""))
        w(f"| `{o['value']}` | {'★' if o.get('pin') else ''}{o['label']} | {o.get('group', '')} | {frag} |")
    w("")

w("## 4. 官方演示的风格描述（按曲风，原文照录，不含歌词）\n")
w("mode：planned = 先由模型规划乐谱再合成（本软件“写词作曲”默认用法），direct = 直接生成。\n")
by_genre = collections.defaultdict(list)
for c in cases:
    by_genre[c["genre"]].append(c)
for g in sorted(by_genre):
    w(f"### {g}")
    for c in by_genre[g]:
        tags = " ".join((c.get("tags") or "").split())
        w(f"- ({c.get('languageLabel')}, {c['mode']}) {tags}")
    w("")

if covers:
    w("## 5. 官方翻唱/改编演示\n")
    w("官方另有改编演示（换词、换风格等），仅列出类型供参考，原曲歌词不收录。\n")
    w("| 标题 | 曲风 | 改编类型 |\n|---|---|---|")
    for c in covers:
        w(f"| {c.get('title')} | {c.get('genre', '')} | {c.get('editType', '')} |")
    w("\n其中 Interstellar 是纯器乐改编（无人声），官方没有公开它的 prompt 和乐谱。")

OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
print(OUT, len("\n".join(L)), "chars")
