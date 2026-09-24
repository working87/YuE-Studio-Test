"""Regenerate the preset catalogue in studio/flow.json (genre / mood / vocal / lead).

Style strings follow the official demo convention: a specific, comma-separated description of
genre, instrumentation, rhythm and feel (official demo prompts: median ~124 characters).
"core" = the genre without its default instruments, used when a lead instrument is chosen.
"pin" options are shown as buttons; the rest go into a grouped drop-down.
"""
import json
from pathlib import Path

G = []  # (value, label, group, style, core, pin)


def genre(value, label, group, style, core=None, pin=False):
    G.append({"value": value, "label": label, "group": group, "style": style, "core": core or style, "pin": pin})


# ---- 流行 ----
genre("pop", "流行 Pop", "流行", "Modern pop, catchy, polished production, punchy drums, bright synths, electric bass, memorable hook",
      "Modern pop, catchy, polished production, punchy drums, memorable hook", True)
genre("ballad", "抒情 Ballad", "流行", "Emotional ballad, slow tempo, heartfelt, piano, lush strings, soft drums, soaring chorus",
      "Emotional ballad, slow tempo, heartfelt, soft drums, soaring climax", True)
genre("dancepop", "舞曲流行 Dance-Pop", "流行", "Dance-pop, upbeat, four-on-the-floor beat, glossy synths, funky bass, club-ready chorus",
      "Dance-pop, upbeat, four-on-the-floor beat, club-ready chorus")
genre("electropop", "电子流行 Electropop", "流行", "Electropop, sparkling synth layers, crisp electronic drums, pulsing bass, modern and bright",
      "Electropop, crisp electronic drums, pulsing bass, modern and bright")
genre("indiepop", "独立流行 Indie Pop", "流行", "Indie pop, jangly guitars, warm analog keys, relaxed groove, dreamy and nostalgic",
      "Indie pop, relaxed groove, dreamy and nostalgic")
genre("dreampop", "梦幻流行 Dream Pop", "流行", "Dream pop, shimmering reverb guitars, hazy synth pads, soft drums, ethereal atmosphere",
      "Dream pop, soft drums, ethereal hazy atmosphere")
genre("softrock", "软摇滚 Soft Rock", "流行", "Soft rock, warm electric piano, clean guitars, gentle drums, smooth 70s feel",
      "Soft rock, gentle drums, smooth 70s feel")
genre("yachtrock", "游艇摇滚 Yacht Rock", "流行", "Yacht rock, smooth Rhodes, clean funky guitar, lush backing harmonies, laid-back groove",
      "Yacht rock, laid-back groove, smooth and polished")
# ---- 华语 / 亚洲 ----
genre("mandopop", "华语流行 C-Pop", "华语与亚洲", "Mandopop, modern Chinese pop production, piano and strings, clean guitars, emotional chorus",
      "Mandopop, modern Chinese pop production, emotional chorus")
genre("guofeng", "古风 国风", "华语与亚洲", "Chinese traditional style, guzheng, dizi, erhu, pipa, pentatonic melody, modern pop arrangement, elegant",
      "Chinese traditional style, pentatonic melody, modern pop arrangement, elegant", True)
genre("guofeng_edm", "国风电子", "华语与亚洲", "Chinese-style electronic, guzheng and dizi over trap drums and deep 808 bass, pentatonic hooks, cinematic drops",
      "Chinese-style electronic, trap drums, deep 808 bass, pentatonic hooks, cinematic drops")
genre("cantopop", "粤语流行 Cantopop", "华语与亚洲", "Cantopop, 90s Hong Kong pop ballad, piano, strings, warm electric guitar, nostalgic",
      "Cantopop, 90s Hong Kong pop, nostalgic")
genre("citypop", "City Pop", "华语与亚洲", "City Pop, 80s Japanese city pop, upbeat, danceable, groovy slap bass, electric guitar, synth, neon city night",
      "City Pop, 80s Japanese city pop, upbeat, danceable, groovy bass, neon city night", True)
genre("jpop", "日系流行 J-Pop", "华语与亚洲", "J-Pop, bright energetic arrangement, fast guitars, synth leads, busy bass, anime-style chorus",
      "J-Pop, bright energetic arrangement, anime-style chorus")
genre("jrock", "动漫摇滚 Anime Rock", "华语与亚洲", "Anime rock, J-rock, driving distorted guitars, fast drums, melodic bass runs, heroic chorus",
      "Anime rock, J-rock, fast drums, heroic chorus")
genre("kpop", "韩流 K-Pop", "华语与亚洲", "K-pop, high-energy production, punchy trap-influenced drums, glossy synths, dynamic genre switches, big hook",
      "K-pop, high-energy production, punchy drums, dynamic switches, big hook")
genre("enka", "演歌 Enka", "华语与亚洲", "Enka, traditional Japanese ballad, shamisen, strings, vibrato-rich melody, melancholic",
      "Enka, traditional Japanese ballad, melancholic")
# ---- 摇滚 / 金属 ----
genre("rock", "摇滚 Rock", "摇滚与金属", "Energetic modern rock, big distorted electric guitars, driving drums, powerful bass, anthemic chorus, heavy rhythm",
      "Energetic modern rock, driving drums, powerful bass, anthemic, heavy rhythm", True)
genre("indierock", "独立摇滚 Indie Rock", "摇滚与金属", "Indie rock, jangly and fuzzy guitars, loose live drums, melodic bass, raw and heartfelt",
      "Indie rock, loose live drums, raw and heartfelt")
genre("poppunk", "流行朋克 Pop Punk", "摇滚与金属", "Pop punk, fast palm-muted power chords, energetic drums, catchy shout-along chorus",
      "Pop punk, fast energetic drums, catchy shout-along chorus")
genre("postrock", "后摇 Post-Rock", "摇滚与金属", "Post-rock, slowly building layers of reverb guitars, crescendos, cinematic dynamics, emotional",
      "Post-rock, slow build, crescendos, cinematic dynamics, emotional")
genre("grunge", "垃圾摇滚 Grunge", "摇滚与金属", "Grunge, sludgy distorted guitars, heavy drums, brooding verses, explosive chorus",
      "Grunge, heavy drums, brooding verses, explosive chorus")
genre("metal", "金属 Metal", "摇滚与金属", "Heavy metal, aggressive, heavily distorted electric guitars, heavy riffs, double kick drums, pounding drums, intense, loud",
      "Heavy metal, aggressive, heavy riffs, double kick drums, pounding drums, intense, loud", True)
genre("numetal", "新金属 Nu Metal", "摇滚与金属", "Nu metal, down-tuned chugging guitars, hip-hop groove drums, turntable scratches, angry verses, huge chorus",
      "Nu metal, hip-hop groove drums, angry verses, huge chorus")
genre("glammetal", "华丽金属 Glam Metal", "摇滚与金属", "80s glam metal, shredding guitar solos, big gated drums, arena-size chorus",
      "80s glam metal, big gated drums, arena-size chorus")
genre("rocknroll", "摇滚乐 Rock & Roll", "摇滚与金属", "50s rock and roll, boogie piano, twangy guitar, upright bass slap, swinging drums",
      "50s rock and roll, swinging rhythm, energetic")
# ---- 电子 ----
genre("edm", "电子 EDM", "电子", "EDM, electronic dance music, four-on-the-floor kick, big synth drops, sidechained pads, rising builds, festival energy",
      "EDM, electronic dance music, four-on-the-floor kick, rising builds, festival energy", True)
genre("house", "浩室 House", "电子", "Deep house, four-on-the-floor groove, warm bassline, chopped piano chords, smooth pads",
      "Deep house, four-on-the-floor groove, warm bassline")
genre("synthwave", "合成器浪潮 Synthwave", "电子", "Synthwave, 80s retro, analog arpeggios, gated reverb drums, neon night drive",
      "Synthwave, 80s retro, gated reverb drums, neon night drive")
genre("futurebass", "未来贝斯 Future Bass", "电子", "Future bass, lush supersaw chords, pitched vocal chops, trap drums, euphoric drops",
      "Future bass, trap drums, euphoric drops")
genre("dubstep", "回响贝斯 Dubstep", "电子", "Dubstep, heavy wobble bass, half-time drums, aggressive drops",
      "Dubstep, half-time drums, aggressive drops")
genre("eurobeat", "欧陆舞曲 Eurobeat", "电子", "Eurobeat, very fast tempo, driving synth bass, stabbing synth leads, high-energy",
      "Eurobeat, very fast tempo, driving, high-energy")
genre("nudisco", "新迪斯科 Nu-Disco", "电子", "Nu-disco, funky bass guitar, disco strings, filtered house beat, groovy",
      "Nu-disco, filtered house beat, groovy")
genre("lofi", "Lo-fi", "电子", "Lo-fi hip hop, chill, dusty drums, warm Rhodes keys, vinyl crackle, mellow, relaxed",
      "Lo-fi hip hop, chill, dusty drums, vinyl crackle, mellow, relaxed", True)
genre("ambient", "氛围 Ambient", "电子", "Ambient, slowly evolving synth textures, soft drones, spacious reverb, calm and meditative",
      "Ambient, spacious, calm and meditative")
# ---- 嘻哈 / R&B ----
genre("hiphop", "嘻哈 Hip-hop", "嘻哈与节奏布鲁斯", "Hip-hop, boom bap drums, deep 808 bass, sampled loop, head-nodding groove, rap style",
      "Hip-hop, boom bap drums, deep 808 bass, head-nodding groove", True)
genre("trap", "陷阱 Trap", "嘻哈与节奏布鲁斯", "Trap, rolling hi-hats, booming 808 bass, dark synth melody, hard-hitting",
      "Trap, rolling hi-hats, booming 808 bass, hard-hitting")
genre("rnb", "R&B", "嘻哈与节奏布鲁斯", "Contemporary R&B, smooth, soulful groove, silky bass, lush electric piano chords, laid-back drums, sensual",
      "Contemporary R&B, smooth, soulful groove, silky bass, laid-back drums", True)
genre("neosoul", "新灵魂 Neo-Soul", "嘻哈与节奏布鲁斯", "Neo-soul, warm Rhodes, jazzy chords, swung drums, round bass, intimate",
      "Neo-soul, jazzy chords, swung drums, intimate")
genre("funk", "放克 Funk", "嘻哈与节奏布鲁斯", "Funk, tight syncopated drums, slap bass, choppy rhythm guitar, horn stabs, groovy",
      "Funk, tight syncopated drums, slap bass, groovy")
genre("disco", "迪斯科 Disco", "嘻哈与节奏布鲁斯", "70s disco, four-on-the-floor, octave bass, lush strings, funky guitar, glittering",
      "70s disco, four-on-the-floor, octave bass, glittering")
# ---- 爵士 / 蓝调 / 灵魂 ----
genre("jazz", "爵士 Jazz", "爵士与蓝调", "Jazz, swing feel, walking upright bass, brushed drums, jazz piano, Rhodes, saxophone, sophisticated harmony",
      "Jazz, swing feel, walking upright bass, brushed drums, sophisticated harmony", True)
genre("bigband", "大乐队摇摆 Big Band", "爵士与蓝调", "Big band swing, brass section, saxophone section, walking bass, swinging drums",
      "Big band swing, walking bass, swinging drums")
genre("bossanova", "波萨诺瓦 Bossa Nova", "爵士与蓝调", "Bossa nova, nylon guitar, soft brushed percussion, gentle syncopation, breezy",
      "Bossa nova, soft brushed percussion, gentle syncopation, breezy")
genre("blues", "蓝调 Blues", "爵士与蓝调", "Blues, 12-bar shuffle, expressive electric guitar licks, harmonica, organ, gritty",
      "Blues, 12-bar shuffle, gritty")
genre("soul", "灵魂乐 Soul", "爵士与蓝调", "Classic soul, Hammond organ, horn section, tight rhythm section, warm and uplifting",
      "Classic soul, tight rhythm section, warm and uplifting")
genre("gospel", "福音 Gospel", "爵士与蓝调", "Gospel, powerful choir, Hammond organ, piano, clapping, uplifting",
      "Gospel, clapping, uplifting")
# ---- 民谣 / 乡村 / 世界 ----
genre("folk", "民谣 Folk", "民谣乡村与世界", "Acoustic folk, fingerpicked acoustic guitar, warm and organic, gentle percussion, intimate, storytelling",
      "Acoustic folk, warm and organic, gentle percussion, intimate, storytelling", True)
genre("country", "乡村 Country", "民谣乡村与世界", "Country, acoustic and electric guitars, pedal steel, fiddle, steady two-step drums",
      "Country, steady two-step drums, heartland feel")
genre("bluegrass", "蓝草 Bluegrass", "民谣乡村与世界", "Bluegrass, banjo, fiddle, mandolin, upright bass, fast picking",
      "Bluegrass, fast picking, lively")
genre("reggae", "雷鬼 Reggae", "民谣乡村与世界", "Reggae, offbeat guitar skank, deep bass, one-drop drums, laid-back",
      "Reggae, one-drop drums, laid-back")
genre("reggaeton", "雷鬼动 Reggaetón", "民谣乡村与世界", "Reggaetón, dembow rhythm, deep bass, Latin percussion, sensual dance groove",
      "Reggaetón, dembow rhythm, sensual dance groove")
genre("latinpop", "拉丁流行 Latin Pop", "民谣乡村与世界", "Latin pop, Spanish guitar, congas and bongos, brass accents, sunny dance rhythm",
      "Latin pop, sunny dance rhythm")
genre("flamenco", "弗拉门戈 Flamenco", "民谣乡村与世界", "Flamenco, rapid Spanish guitar, palmas hand claps, cajón, passionate",
      "Flamenco, palmas hand claps, cajón, passionate")
genre("afrobeats", "非洲节拍 Afrobeats", "民谣乡村与世界", "Afrobeats, syncopated percussion, log drum, warm bass, bright guitar riffs, joyful",
      "Afrobeats, syncopated percussion, warm bass, joyful")
genre("celtic", "凯尔特 Celtic", "民谣乡村与世界", "Celtic folk, tin whistle, fiddle, bodhrán, acoustic guitar, jig rhythm",
      "Celtic folk, jig rhythm, lively")
# ---- 古典 / 影视 / 其他 ----
genre("classical", "古典 Classical", "古典影视与其他", "Classical orchestral, strings, woodwinds, French horns, timpani, expressive dynamics",
      "Classical, expressive dynamics, elegant")
genre("cinematic", "电影配乐 Cinematic", "古典影视与其他", "Epic cinematic score, full orchestra, taiko drums, choir, soaring brass, huge build",
      "Epic cinematic score, taiko drums, huge build")
genre("musical", "音乐剧 Musical Theatre", "古典影视与其他", "Broadway musical theatre, piano and orchestra, dramatic dynamics, theatrical storytelling",
      "Broadway musical theatre, dramatic dynamics, theatrical storytelling")
genre("children", "儿歌 Children's Song", "古典影视与其他", "Children's song, playful, simple melody, ukulele, glockenspiel, hand claps, cheerful",
      "Children's song, playful, simple melody, cheerful")
genre("acappella", "阿卡贝拉 A Cappella", "古典影视与其他", "A cappella, layered vocal harmonies, vocal percussion, no instruments",
      "A cappella, layered vocal harmonies, vocal percussion")

MOODS = [
    ("warm", "温暖治愈", "warm, hopeful, comforting", True), ("sad", "伤感", "melancholic, bittersweet", True),
    ("hype", "热血燃", "energetic, uplifting, powerful", True), ("romantic", "浪漫甜", "romantic, sweet", True),
    ("chill", "慵懒 Chill", "laid-back, relaxed", True), ("epic", "史诗感", "epic, cinematic, grand", True),
    ("playful", "俏皮可爱", "playful, cute, bouncy", True),
    ("nostalgic", "怀旧", "nostalgic, wistful", False), ("dreamy", "梦幻", "dreamy, floating, ethereal", False),
    ("dark", "暗黑", "dark, tense, ominous", False), ("angry", "愤怒", "angry, aggressive, rebellious", False),
    ("lonely", "孤独", "lonely, introspective, quiet", False), ("hopeful", "励志", "inspiring, triumphant, uplifting", False),
    ("sexy", "性感", "sensual, seductive, smooth", False), ("mysterious", "神秘", "mysterious, suspenseful", False),
    ("peaceful", "宁静", "peaceful, serene, gentle", False), ("party", "派对", "party, euphoric, celebratory", False),
]
VOCALS = [
    ("f_bright", "清亮女声", "bright clear female vocal", True, "女声"), ("f_soft", "温柔气声女声", "soft breathy female vocal", True, "女声"),
    ("f_power", "高亢有力女声", "powerful belting female vocal, wide range", False, "女声"),
    ("f_sweet", "甜美少女音", "sweet youthful female vocal, cute", False, "女声"),
    ("f_husky", "烟嗓女声", "husky smoky female vocal, jazzy", False, "女声"),
    ("f_whisper", "耳语女声", "intimate whispery female vocal", False, "女声"),
    ("m_warm", "温暖男声", "warm male vocal", True, "男声"), ("m_raspy", "沙哑有力男声", "raspy powerful male vocal", True, "男声"),
    ("m_deep", "低沉男中音", "deep baritone male vocal", False, "男声"),
    ("m_tenor", "高亢男高音", "soaring tenor male vocal, high notes", False, "男声"),
    ("m_falsetto", "假声男声", "smooth male falsetto vocal", False, "男声"),
    ("m_soft", "温柔男声", "soft gentle male vocal", False, "男声"),
    ("rap_m", "男声说唱", "male rap vocal, rhythmic flow", False, "说唱与特殊"), ("rap_f", "女声说唱", "female rap vocal, confident flow", False, "说唱与特殊"),
    ("scream", "嘶吼（金属）", "harsh screamed vocals", False, "说唱与特殊"), ("opera", "美声", "operatic bel canto vocal", False, "说唱与特殊"),
    ("child", "童声", "children's vocal", False, "说唱与特殊"),
    ("duet", "男女对唱（不稳定）", "male and female duet vocals", True, "合唱与对唱"),
    ("choir", "合唱感", "layered choir vocals", True, "合唱与对唱"),
    ("boyband", "男团合唱", "boy band harmonies, multiple male vocals", False, "合唱与对唱"),
]
LEADS = [
    ("piano", "钢琴", "piano carries the melody, expressive solo piano, prominent piano lead", True, "键盘"),
    ("rhodes", "电钢琴", "Rhodes electric piano carries the melody", False, "键盘"),
    ("organ", "管风琴/哈蒙德", "Hammond organ carries the melody", False, "键盘"),
    ("synth", "合成器", "synthesizer carries the melody, prominent synth lead, analog synth", True, "键盘"),
    ("guitar", "电吉他", "electric guitar carries the melody, prominent lead guitar, melodic guitar solo", True, "吉他与弦乐"),
    ("acoustic", "木吉他", "acoustic guitar carries the melody, fingerpicked lead", False, "吉他与弦乐"),
    ("strings", "弦乐团", "string orchestra carries the melody, soaring violins and cellos, cinematic strings", True, "吉他与弦乐"),
    ("violin", "小提琴", "violin carries the melody, expressive solo violin lead", False, "吉他与弦乐"),
    ("cello", "大提琴", "cello carries the melody, warm solo cello lead", False, "吉他与弦乐"),
    ("sax", "萨克斯", "saxophone carries the melody, prominent tenor saxophone lead, saxophone solo", True, "管乐"),
    ("trumpet", "小号", "trumpet carries the melody, bright trumpet lead", False, "管乐"),
    ("flute", "长笛", "flute carries the melody, airy flute lead", False, "管乐"),
    ("harmonica", "口琴", "harmonica carries the melody", False, "管乐"),
    ("guzheng", "古筝", "guzheng carries the melody, prominent Chinese zither lead", True, "民族乐器"),
    ("erhu", "二胡", "erhu carries the melody, expressive Chinese erhu lead", False, "民族乐器"),
    ("pipa", "琵琶", "pipa carries the melody, plucked Chinese pipa lead", False, "民族乐器"),
    ("dizi", "笛子", "dizi bamboo flute carries the melody", False, "民族乐器"),
    ("musicbox", "八音盒", "music box carries the melody, delicate", False, "其他"),
]

path = Path(__file__).resolve().parents[1] / "studio" / "flow.json"
flow = json.loads(path.read_text(encoding="utf-8"))
steps = flow["steps"]
steps["genre"]["options"] = G
steps["mood"]["options"] = [{"value": v, "label": l, "style": s, "pin": p} for v, l, s, p in MOODS]
steps["vocal"]["options"] = [{"value": v, "label": l, "style": s, "pin": p, "group": g,
                              **({"desc": "实测模型通常只唱出一个声部，想要对唱建议分两次生成"} if v == "duet" else {})}
                             for v, l, s, p, g in VOCALS]
# English names for section tags like the official demos' "[Intro: Piano & Flute]" (哼唱 → 纯音乐).
LEAD_TAGS = {"piano": "Piano", "rhodes": "Electric Piano", "organ": "Organ", "synth": "Synth",
             "guitar": "Electric Guitar", "acoustic": "Acoustic Guitar", "strings": "Strings", "violin": "Violin",
             "cello": "Cello", "sax": "Saxophone", "trumpet": "Trumpet", "flute": "Flute", "harmonica": "Harmonica",
             "guzheng": "Guzheng", "erhu": "Erhu", "pipa": "Pipa", "dizi": "Dizi", "musicbox": "Music Box"}
steps["lead"]["options"] = [{"value": v, "label": l, "style": s, "pin": p, "group": g, "tag": LEAD_TAGS[v]}
                            for v, l, s, p, g in LEADS]
# Update rather than replace: other settings on the step (e.g. agent_skip) must survive a regeneration.
steps["extra"] = {**steps.get("extra", {}), "type": "text", "optional": True,
                  "q": "补充描述（可选）：还想要什么具体效果？例如“前奏只有钢琴，副歌加入弦乐和鼓”“带点黑胶质感”"}
steps["extra"].setdefault("agent_skip", True)
for key, feature in flow["features"].items():
    if key != "remix" and "extra" not in feature["steps"]:
        feature["steps"].insert(feature["steps"].index("variants"), "extra")
path.write_text(json.dumps(flow, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"genres {len(G)} (pinned {sum(g['pin'] for g in G)}), moods {len(MOODS)}, vocals {len(VOCALS)}, leads {len(LEADS)}")
