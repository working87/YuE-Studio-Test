# YuE2 风格描述参考（给 agent 读）

本文件由 `scripts/build_style_guide.py` 从官方演示页数据和 `studio/flow.json` 生成。用于：帮用户把一句口语需求写成好的 style（风格描述），或在预设之外自由发挥。

## 1. 模型怎么读风格描述

- 官方演示共 99 首（全部带人声），70 种曲风；语言：English 56, Chinese 31, Japanese 9, Russian 1, Spanish 1, Korean 1。
- 风格描述长度：中位数 124 字符，最短 4，最长 999。两种写法都有效：逗号分隔的标签（`funk, upbeat, male vocal`），或一段完整的编曲描述（从前奏写到尾奏）。
- 推荐顺序：曲风 → 核心乐器 → 情绪 → 人声（性别/音色/唱法）→ 速度/节奏感 → 制作质感。本软件会自动把语言（Mandarin/Cantonese/English...）加在最前面，不用自己写。
- 实测：模型强烈跟随“唱的那条旋律”，伴奏（Ins 声部）只弱跟随。所以“某乐器演奏主旋律”这类描述只能影响音色和编曲，不能保证乐器逐音复现哼唱。
- 不要在 style 里写真实歌手名字冒充原唱；描述音色和唱法即可（例如 breathy airy female vocal）。
- 歌词里的段落标签可以带乐器注释，官方就这么写，例如 `[Intro: Piano & Flute]`、`[Guitar Solo]`；纯器乐段用 `[Instrumental Break]`、`[Interlude]`，段内不写歌词。

## 2. 段落标签（官方演示统计）

| 标签 | 次数 |
|---|---|
| `[Chorus]` | 162 |
| `[Pre-Chorus]` | 56 |
| `[Bridge]` | 48 |
| `[Verse 2]` | 46 |
| `[Verse 1]` | 40 |
| `[Outro]` | 40 |
| `[Male Vocals]` | 25 |
| `[Intro]` | 23 |
| `[Interlude]` | 18 |
| `[Verse]` | 16 |
| `[Verse 3]` | 8 |
| `[Guitar Solo]` | 8 |
| `[Prechorus]` | 8 |
| `[Instrumental Break]` | 7 |
| `[Verse1]` | 7 |
| `[Verse2]` | 7 |
| `[End]` | 6 |
| `[Verse 4]` | 4 |
| `[instrumental intro]` | 4 |
| `[Final Chorus]` | 4 |
| `[Chorus – Both]` | 3 |
| `[Synth melody with vocal ad-libs]` | 3 |
| `[Bridge – Call & Response / Dance break]` | 2 |
| `[Pre‐Chorus – Sung]` | 2 |
| `[chorus]` | 2 |
| `[DRAGONZILLA — MONSTER VOX]` | 2 |
| `[Verse 5]` | 2 |
| `[Intro - Big Band Fanfare]` | 2 |
| `[Intro – instrumental groove]` | 1 |
| `[Verse 1 – Male voice (raspy, relaxed)]` | 1 |

带乐器/演唱注释的标签示例：`[Chorus: All]`、`[Intro: Piano & Flute]`、`[Instrumental Break: Piano, Flute, Drums]`、`[Outro: Piano & Flute]`、`[Spoken: B'khatma]`、`[Intro: Acoustic Guitar Melody]`、`[Outro: Extended Guitar Solo and Instrumental Fade]`、`[Instrumental Introduction: Powerful drum kit and bass rhythms accompanied by towering suona and flute melodies]`、`[Chorus: The melody shifts to a more heroic theme, with the flute and erhu interacting.]`、`[Chorus: Complete Collection.]`、`[Section Two: The erhu takes the lead in responding with the suona. The bass and drums maintain a tight and energetic rhythm.]`、`[Chorus: Another complete collection.]`、`[Bridge: The melodious erhu and flute duet in a suspenseful bass and dramatic drum kit sound, creating vitality.]`、`[The final chorus: Play with all your might.]`、`[Narrator: With the final powerful note of the collision between the suona and the drum kit, the music gradually fades away.]`、`[Verse 1: Sun Wukong]`、`[Pre-Chorus: Tang Sanzang]`、`[Verse 2: Zhu Bajie & Sha Wujing]`、`[Bridge: Xiao Bailong]`、`[Final Chorus: All]`、`[Outro: All]`、`[GENRES: Funk Soul, Funk Jazz Fusion]`、`[STYLE: Virtuoso, Fusion, Instrumental, Sofisticado]`、`[MOOD: Intelectual, Groovy, Exploratório, Virtuoso]`、`[TEMPO: 90–140 BPM]`

## 3. 本软件的预设（向导选项）

向导的 value 必须用下表的 value；表外的想法可以直接写英文描述作为自由文本（custom_allowed 为真时）。`core` 是有旋律输入时（哼唱/参考歌曲）用的精简版，避免乐器描述把旋律带跑。

### 曲风 `genre`（61 项，★=界面常用）

| value | 名称 | 分组 | style 片段 |
|---|---|---|---|
| `pop` | ★流行 Pop | 流行 | Modern pop, catchy, polished production, punchy drums, bright synths, electric bass, memorable hook |
| `ballad` | ★抒情 Ballad | 流行 | Emotional ballad, slow tempo, heartfelt, piano, lush strings, soft drums, soaring chorus |
| `dancepop` | 舞曲流行 Dance-Pop | 流行 | Dance-pop, upbeat, four-on-the-floor beat, glossy synths, funky bass, club-ready chorus |
| `electropop` | 电子流行 Electropop | 流行 | Electropop, sparkling synth layers, crisp electronic drums, pulsing bass, modern and bright |
| `indiepop` | 独立流行 Indie Pop | 流行 | Indie pop, jangly guitars, warm analog keys, relaxed groove, dreamy and nostalgic |
| `dreampop` | 梦幻流行 Dream Pop | 流行 | Dream pop, shimmering reverb guitars, hazy synth pads, soft drums, ethereal atmosphere |
| `softrock` | 软摇滚 Soft Rock | 流行 | Soft rock, warm electric piano, clean guitars, gentle drums, smooth 70s feel |
| `yachtrock` | 游艇摇滚 Yacht Rock | 流行 | Yacht rock, smooth Rhodes, clean funky guitar, lush backing harmonies, laid-back groove |
| `mandopop` | 华语流行 C-Pop | 华语与亚洲 | Mandopop, modern Chinese pop production, piano and strings, clean guitars, emotional chorus |
| `guofeng` | ★古风 国风 | 华语与亚洲 | Chinese traditional style, guzheng, dizi, erhu, pipa, pentatonic melody, modern pop arrangement, elegant |
| `guofeng_edm` | 国风电子 | 华语与亚洲 | Chinese-style electronic, guzheng and dizi over trap drums and deep 808 bass, pentatonic hooks, cinematic drops |
| `cantopop` | 粤语流行 Cantopop | 华语与亚洲 | Cantopop, 90s Hong Kong pop ballad, piano, strings, warm electric guitar, nostalgic |
| `citypop` | ★City Pop | 华语与亚洲 | City Pop, 80s Japanese city pop, upbeat, danceable, groovy slap bass, electric guitar, synth, neon city night |
| `jpop` | 日系流行 J-Pop | 华语与亚洲 | J-Pop, bright energetic arrangement, fast guitars, synth leads, busy bass, anime-style chorus |
| `jrock` | 动漫摇滚 Anime Rock | 华语与亚洲 | Anime rock, J-rock, driving distorted guitars, fast drums, melodic bass runs, heroic chorus |
| `kpop` | 韩流 K-Pop | 华语与亚洲 | K-pop, high-energy production, punchy trap-influenced drums, glossy synths, dynamic genre switches, big hook |
| `enka` | 演歌 Enka | 华语与亚洲 | Enka, traditional Japanese ballad, shamisen, strings, vibrato-rich melody, melancholic |
| `rock` | ★摇滚 Rock | 摇滚与金属 | Energetic modern rock, big distorted electric guitars, driving drums, powerful bass, anthemic chorus, heavy rhythm |
| `indierock` | 独立摇滚 Indie Rock | 摇滚与金属 | Indie rock, jangly and fuzzy guitars, loose live drums, melodic bass, raw and heartfelt |
| `poppunk` | 流行朋克 Pop Punk | 摇滚与金属 | Pop punk, fast palm-muted power chords, energetic drums, catchy shout-along chorus |
| `postrock` | 后摇 Post-Rock | 摇滚与金属 | Post-rock, slowly building layers of reverb guitars, crescendos, cinematic dynamics, emotional |
| `grunge` | 垃圾摇滚 Grunge | 摇滚与金属 | Grunge, sludgy distorted guitars, heavy drums, brooding verses, explosive chorus |
| `metal` | ★金属 Metal | 摇滚与金属 | Heavy metal, aggressive, heavily distorted electric guitars, heavy riffs, double kick drums, pounding drums, intense, loud |
| `numetal` | 新金属 Nu Metal | 摇滚与金属 | Nu metal, down-tuned chugging guitars, hip-hop groove drums, turntable scratches, angry verses, huge chorus |
| `glammetal` | 华丽金属 Glam Metal | 摇滚与金属 | 80s glam metal, shredding guitar solos, big gated drums, arena-size chorus |
| `rocknroll` | 摇滚乐 Rock & Roll | 摇滚与金属 | 50s rock and roll, boogie piano, twangy guitar, upright bass slap, swinging drums |
| `edm` | ★电子 EDM | 电子 | EDM, electronic dance music, four-on-the-floor kick, big synth drops, sidechained pads, rising builds, festival energy |
| `house` | 浩室 House | 电子 | Deep house, four-on-the-floor groove, warm bassline, chopped piano chords, smooth pads |
| `synthwave` | 合成器浪潮 Synthwave | 电子 | Synthwave, 80s retro, analog arpeggios, gated reverb drums, neon night drive |
| `futurebass` | 未来贝斯 Future Bass | 电子 | Future bass, lush supersaw chords, pitched vocal chops, trap drums, euphoric drops |
| `dubstep` | 回响贝斯 Dubstep | 电子 | Dubstep, heavy wobble bass, half-time drums, aggressive drops |
| `eurobeat` | 欧陆舞曲 Eurobeat | 电子 | Eurobeat, very fast tempo, driving synth bass, stabbing synth leads, high-energy |
| `nudisco` | 新迪斯科 Nu-Disco | 电子 | Nu-disco, funky bass guitar, disco strings, filtered house beat, groovy |
| `lofi` | ★Lo-fi | 电子 | Lo-fi hip hop, chill, dusty drums, warm Rhodes keys, vinyl crackle, mellow, relaxed |
| `ambient` | 氛围 Ambient | 电子 | Ambient, slowly evolving synth textures, soft drones, spacious reverb, calm and meditative |
| `hiphop` | ★嘻哈 Hip-hop | 嘻哈与节奏布鲁斯 | Hip-hop, boom bap drums, deep 808 bass, sampled loop, head-nodding groove, rap style |
| `trap` | 陷阱 Trap | 嘻哈与节奏布鲁斯 | Trap, rolling hi-hats, booming 808 bass, dark synth melody, hard-hitting |
| `rnb` | ★R&B | 嘻哈与节奏布鲁斯 | Contemporary R&B, smooth, soulful groove, silky bass, lush electric piano chords, laid-back drums, sensual |
| `neosoul` | 新灵魂 Neo-Soul | 嘻哈与节奏布鲁斯 | Neo-soul, warm Rhodes, jazzy chords, swung drums, round bass, intimate |
| `funk` | 放克 Funk | 嘻哈与节奏布鲁斯 | Funk, tight syncopated drums, slap bass, choppy rhythm guitar, horn stabs, groovy |
| `disco` | 迪斯科 Disco | 嘻哈与节奏布鲁斯 | 70s disco, four-on-the-floor, octave bass, lush strings, funky guitar, glittering |
| `jazz` | ★爵士 Jazz | 爵士与蓝调 | Jazz, swing feel, walking upright bass, brushed drums, jazz piano, Rhodes, saxophone, sophisticated harmony |
| `bigband` | 大乐队摇摆 Big Band | 爵士与蓝调 | Big band swing, brass section, saxophone section, walking bass, swinging drums |
| `bossanova` | 波萨诺瓦 Bossa Nova | 爵士与蓝调 | Bossa nova, nylon guitar, soft brushed percussion, gentle syncopation, breezy |
| `blues` | 蓝调 Blues | 爵士与蓝调 | Blues, 12-bar shuffle, expressive electric guitar licks, harmonica, organ, gritty |
| `soul` | 灵魂乐 Soul | 爵士与蓝调 | Classic soul, Hammond organ, horn section, tight rhythm section, warm and uplifting |
| `gospel` | 福音 Gospel | 爵士与蓝调 | Gospel, powerful choir, Hammond organ, piano, clapping, uplifting |
| `folk` | ★民谣 Folk | 民谣乡村与世界 | Acoustic folk, fingerpicked acoustic guitar, warm and organic, gentle percussion, intimate, storytelling |
| `country` | 乡村 Country | 民谣乡村与世界 | Country, acoustic and electric guitars, pedal steel, fiddle, steady two-step drums |
| `bluegrass` | 蓝草 Bluegrass | 民谣乡村与世界 | Bluegrass, banjo, fiddle, mandolin, upright bass, fast picking |
| `reggae` | 雷鬼 Reggae | 民谣乡村与世界 | Reggae, offbeat guitar skank, deep bass, one-drop drums, laid-back |
| `reggaeton` | 雷鬼动 Reggaetón | 民谣乡村与世界 | Reggaetón, dembow rhythm, deep bass, Latin percussion, sensual dance groove |
| `latinpop` | 拉丁流行 Latin Pop | 民谣乡村与世界 | Latin pop, Spanish guitar, congas and bongos, brass accents, sunny dance rhythm |
| `flamenco` | 弗拉门戈 Flamenco | 民谣乡村与世界 | Flamenco, rapid Spanish guitar, palmas hand claps, cajón, passionate |
| `afrobeats` | 非洲节拍 Afrobeats | 民谣乡村与世界 | Afrobeats, syncopated percussion, log drum, warm bass, bright guitar riffs, joyful |
| `celtic` | 凯尔特 Celtic | 民谣乡村与世界 | Celtic folk, tin whistle, fiddle, bodhrán, acoustic guitar, jig rhythm |
| `classical` | 古典 Classical | 古典影视与其他 | Classical orchestral, strings, woodwinds, French horns, timpani, expressive dynamics |
| `cinematic` | 电影配乐 Cinematic | 古典影视与其他 | Epic cinematic score, full orchestra, taiko drums, choir, soaring brass, huge build |
| `musical` | 音乐剧 Musical Theatre | 古典影视与其他 | Broadway musical theatre, piano and orchestra, dramatic dynamics, theatrical storytelling |
| `children` | 儿歌 Children's Song | 古典影视与其他 | Children's song, playful, simple melody, ukulele, glockenspiel, hand claps, cheerful |
| `acappella` | 阿卡贝拉 A Cappella | 古典影视与其他 | A cappella, layered vocal harmonies, vocal percussion, no instruments |

### 情绪 `mood`（17 项，★=界面常用）

| value | 名称 | 分组 | style 片段 |
|---|---|---|---|
| `warm` | ★温暖治愈 |  | warm, hopeful, comforting |
| `sad` | ★伤感 |  | melancholic, bittersweet |
| `hype` | ★热血燃 |  | energetic, uplifting, powerful |
| `romantic` | ★浪漫甜 |  | romantic, sweet |
| `chill` | ★慵懒 Chill |  | laid-back, relaxed |
| `epic` | ★史诗感 |  | epic, cinematic, grand |
| `playful` | ★俏皮可爱 |  | playful, cute, bouncy |
| `nostalgic` | 怀旧 |  | nostalgic, wistful |
| `dreamy` | 梦幻 |  | dreamy, floating, ethereal |
| `dark` | 暗黑 |  | dark, tense, ominous |
| `angry` | 愤怒 |  | angry, aggressive, rebellious |
| `lonely` | 孤独 |  | lonely, introspective, quiet |
| `hopeful` | 励志 |  | inspiring, triumphant, uplifting |
| `sexy` | 性感 |  | sensual, seductive, smooth |
| `mysterious` | 神秘 |  | mysterious, suspenseful |
| `peaceful` | 宁静 |  | peaceful, serene, gentle |
| `party` | 派对 |  | party, euphoric, celebratory |

### 人声 `vocal`（20 项，★=界面常用）

| value | 名称 | 分组 | style 片段 |
|---|---|---|---|
| `f_bright` | ★清亮女声 | 女声 | bright clear female vocal |
| `f_soft` | ★温柔气声女声 | 女声 | soft breathy female vocal |
| `f_power` | 高亢有力女声 | 女声 | powerful belting female vocal, wide range |
| `f_sweet` | 甜美少女音 | 女声 | sweet youthful female vocal, cute |
| `f_husky` | 烟嗓女声 | 女声 | husky smoky female vocal, jazzy |
| `f_whisper` | 耳语女声 | 女声 | intimate whispery female vocal |
| `m_warm` | ★温暖男声 | 男声 | warm male vocal |
| `m_raspy` | ★沙哑有力男声 | 男声 | raspy powerful male vocal |
| `m_deep` | 低沉男中音 | 男声 | deep baritone male vocal |
| `m_tenor` | 高亢男高音 | 男声 | soaring tenor male vocal, high notes |
| `m_falsetto` | 假声男声 | 男声 | smooth male falsetto vocal |
| `m_soft` | 温柔男声 | 男声 | soft gentle male vocal |
| `rap_m` | 男声说唱 | 说唱与特殊 | male rap vocal, rhythmic flow |
| `rap_f` | 女声说唱 | 说唱与特殊 | female rap vocal, confident flow |
| `scream` | 嘶吼（金属） | 说唱与特殊 | harsh screamed vocals |
| `opera` | 美声 | 说唱与特殊 | operatic bel canto vocal |
| `child` | 童声 | 说唱与特殊 | children's vocal |
| `duet` | ★男女对唱（不稳定） | 合唱与对唱 | male and female duet vocals |
| `choir` | ★合唱感 | 合唱与对唱 | layered choir vocals |
| `boyband` | 男团合唱 | 合唱与对唱 | boy band harmonies, multiple male vocals |

### 主奏乐器（纯音乐） `lead`（18 项，★=界面常用）

| value | 名称 | 分组 | style 片段 |
|---|---|---|---|
| `piano` | ★钢琴 | 键盘 | piano carries the melody, expressive solo piano, prominent piano lead |
| `rhodes` | 电钢琴 | 键盘 | Rhodes electric piano carries the melody |
| `organ` | 管风琴/哈蒙德 | 键盘 | Hammond organ carries the melody |
| `synth` | ★合成器 | 键盘 | synthesizer carries the melody, prominent synth lead, analog synth |
| `guitar` | ★电吉他 | 吉他与弦乐 | electric guitar carries the melody, prominent lead guitar, melodic guitar solo |
| `acoustic` | 木吉他 | 吉他与弦乐 | acoustic guitar carries the melody, fingerpicked lead |
| `strings` | ★弦乐团 | 吉他与弦乐 | string orchestra carries the melody, soaring violins and cellos, cinematic strings |
| `violin` | 小提琴 | 吉他与弦乐 | violin carries the melody, expressive solo violin lead |
| `cello` | 大提琴 | 吉他与弦乐 | cello carries the melody, warm solo cello lead |
| `sax` | ★萨克斯 | 管乐 | saxophone carries the melody, prominent tenor saxophone lead, saxophone solo |
| `trumpet` | 小号 | 管乐 | trumpet carries the melody, bright trumpet lead |
| `flute` | 长笛 | 管乐 | flute carries the melody, airy flute lead |
| `harmonica` | 口琴 | 管乐 | harmonica carries the melody |
| `guzheng` | ★古筝 | 民族乐器 | guzheng carries the melody, prominent Chinese zither lead |
| `erhu` | 二胡 | 民族乐器 | erhu carries the melody, expressive Chinese erhu lead |
| `pipa` | 琵琶 | 民族乐器 | pipa carries the melody, plucked Chinese pipa lead |
| `dizi` | 笛子 | 民族乐器 | dizi bamboo flute carries the melody |
| `musicbox` | 八音盒 | 其他 | music box carries the melody, delicate |

### 速度 `tempo`（6 项，★=界面常用）

| value | 名称 | 分组 | style 片段 |
|---|---|---|---|
| `follow` | 跟随原曲/哼唱 |  |  |
| `70` | 慢 ~70 BPM |  | 70 BPM |
| `88` | 中慢 ~88 BPM |  | 88 BPM |
| `108` | 中速 ~108 BPM |  | 108 BPM |
| `128` | 快 ~128 BPM |  | 128 BPM |
| `150` | 很快 ~150 BPM |  | 150 BPM |

### 语言 `language`（6 项，★=界面常用）

| value | 名称 | 分组 | style 片段 |
|---|---|---|---|
| `auto` | 跟随歌词 |  | 按你写的歌词自动识别语言 |
| `zh` | 普通话 |  | Mandarin |
| `yue` | 粤语（实验） |  | Cantonese |
| `en` | 英语 |  | English |
| `ja` | 日语（实验） |  | Japanese |
| `ko` | 韩语（实验） |  | Korean |

## 4. 官方演示的风格描述（按曲风，原文照录，不含歌词）

mode：planned = 先由模型规划乐谱再合成（本软件“写词作曲”默认用法），direct = 直接生成。

### Afro Trap
- (English, direct) (音樂風格: 強勁的Trap節拍主導,搭配旋律性十足的Afro合成器琶音。男聲說唱部分充滿力量,副歌則轉為絲滑的R&B演唱,形成強烈對比。大量的混響和延遲效果,營造沙漠與都市的空間感。)

### Afro-Jazz
- (English, planned) Funk Soul, Funk Jazz Fusion - Virtuoso, Fusion, Instrumental, Sofisticado , Piano Acustic , emotion, female

### Alternative Dance
- (English, planned) Dark Synthpop / 1980s New Wave / Darkwave Mid-tempo, hypnotic groove Driving rhythmic analog synth bass sequence Classic 80s drum machine with steady pulse Minimalist verses, emotional chorus lift Atmospheric pads, subtle arpeggiators Short repeating melodic synth hook Moody, obsessive, intimate tone Male baritone vocals, calm and emotional British accent Catchy, repetitive chorus that feels compulsive Depeche Mode–inspired but original

### Ambient
- (Chinese, planned) New Age, ethereal, acoustic guitar, piano, uplifting, spiritual, grounding, nature, serene

### Arabic Pop
- (English, direct) A modern Arabic pop track with a strong R&B and trap influence. The arrangement is built around a clean, nylon-string acoustic guitar playing a melancholic, Spanish-inflected melody. This is contrasted by a hard-hitting trap beat featuring a deep 808 bass, crisp hi-hats, and a sharp snare. The lead female vocal is confident and assertive, delivered with a rhythmic flow and layered with harmonizing backing vocals and echoed ad-libs that add depth. The track builds to a powerful chorus before transitioning into a more reflective bridge and a stripped-down outro, concluding with the solo acoustic guitar and the sound of a book closing.

### Bachata
- (English, planned) reggaeton, salsa, bachata, latin pop, cumbia

### Barbershop
- (English, planned) Upbeat 1940s barbershop quartet a cappella song. Four male harmony voices (lead, tenor, baritone, bass). Playful swing rhythm, finger snaps, bright close chords, vintage nightclub vibe, fun and classy lyrics about having a good time out on the town. No instruments.
- (English, planned) The song features a barbershop quartet a cappella arrangement, with bright, tightly synchronized male vocals weaving rich close harmonies. An upbeat tempo and clever swing rhythm bring a buoyant energy, while playful dynamics and crisp phrasing create a sharp, intellectual satire mood.

### Bhangra
- (English, planned) An inspirational hip-hop track built on a foundation of intricate, flamenco-style nylon-string acoustic guitar melodies and a steady, mid-tempo beat combining a solid kick drum with hand percussion. A confident male vocalist delivers rhythmic, sung-rap verses in Punjabi, with a clear and determined tone. The chorus is anthemic and memorable, reinforced by subtle vocal layers. The arrangement features instrumental breaks that showcase the virtuosic guitar work, and a later section introduces a more intense, faster-paced rap flow. The track concludes with an atmospheric outro, where the beat fades away, leaving the guitar and layered, whispered vocals to bring the song to a reflective close.

### Big Band
- (Chinese, planned) happy, retro, Emotion, Ethereal, bold, Strange, Guitar
- (Chinese, planned) Swing Jazz, upbeat saxophone riff, fingerstyle jazz guitar, playful, ironic, moderate groove, smooth male vocals, vintage 1950s mix
- (Chinese, planned) An upbeat and celebratory big band swing arrangement with a festive Christmas theme. The track is driven by a classic swing rhythm section featuring a walking upright bass, lively drums with prominent ride cymbals, and energetic piano comping. A powerful female lead vocal soars over a full brass section of trumpets and saxophones that deliver punchy stabs and harmonized melodies. The song features a dynamic structure with verses and powerful choruses, a brief, reflective bridge, and a short, playful chiptune-style synth break before a grand finale with a classic big band flourish.
- (Chinese, planned) Genre: Jazz-Pop,Swing,Comedy Music Style: Whimsical,playful,upbeat,vintage,comedic,reminiscent of a silent film era soundtrack,with a touch of musical theater. Similar to the playful energy of "Mr. Sandman" by The Chordettes or the style of "特大号鞋子". Instrumentation: Upright bass (slap bass),light and crisp drums (brush strokes),playful piano,trumpet stabs,clarinet,xylophone,sound effects (slide whistle,bicycle horn,quirky footsteps). Structure: The song follows a clear structure: [Verse 1] [Pre-Chorus] [Chorus] [Verse 2] [Bridge] [Chorus] [Outro]. Description: A male vocalist with a charismatic,smiling,and slightly theatrical voice,half-singing half-speaking the lyrics with a lot of character and playful exaggeration. The mood is lighthearted,humorous,and rebellious against boredom through absurdity. The tempo is upbeat and bouncy.

### Bluegrass
- (English, direct) Starts with lively banjo picking and fiddle lines weaving melodic motifs, joined by upright bass and brisk acoustic guitar. Mandolin and harmonica add sparkle throughout. Festive group harmonies and bursts of handclaps drive soaring choruses, building a spirited bluegrass Christmas atmosphere.
- (English, planned) [Bluegrass gospel, guitar, banjo, folk, fast pace, banjo, violin, mostly banjo and violin

### Boogie Woogie
- (English, planned) Boogie woogie style of the 1930s, fast fun, virtuoso, piano dialogue and soft, muffled female vocals.
- (English, planned) male vocals, Anime, Orchestra jazz, A smooth creepy beat of a hunter hunting his prey as he laughs As he sings

### Boy Band
- (English, direct) pop, synth-driven with a playful bassline and shimmering pads

### Celtic Rock
- (English, direct) Boogie Celtic, Funky House, influenced by traditional Irish folk music. Joyful, spirited, celebratory, warm, communal, and deeply connected. Evokes a sense of shared heritage and vibrant energy. English Driving bodhrán, lively fiddle, boogie piano, electric guitar chords, layered vocal harmonies, and subtle Celtic flute accents. 126 BPM, steady 4/4 beat with a syncopated rhythm. Gentle Intro – Fiddle & Piano Build – Energetic Main Section with layered vocals – Instrumental Break – Gradual Outro featuring bodhrán and flute. A candlelit hall, dancers twirling, raised tankards, a bonfire crackling under a starry sky, and laughter echoing. Immersive, celebratory, and soulful. “A dance for the ages.” Avoid heavy distortion.

### Christian Rock
- (Chinese, direct) A polished Mandopop ballad opens with a clean, melodic electric guitar line playing over gentle acoustic guitar strumming. A clear, earnest male vocal enters, delivering an inspirational message with a smooth, heartfelt tone. The arrangement builds into a powerful, uplifting chorus where a full band—comprising steady drums, a solid bassline, and atmospheric synth pads—joins in, supporting layered vocal harmonies that add depth and emotional weight. The song follows a classic verse-chorus structure with a dynamic arc, culminating in a soaring final chorus and resolving with a gentle piano arpeggio and a final, reflective vocal phrase.

### City Pop
- (Chinese, planned) City Pop, upbeat disco funk, synth bass, electric piano, shimmering guitars, driving rhythm section, neon-lit night drive, retro-futuristic euphoria, 1980s Tokyo vibe, carefree summer energy

### Classical Music
- (English, planned) Contemporary Christian

### Comedy
- (English, planned) Pop genre, Happy mood, Live vocal style, Upbeat production
- (English, planned) Country male vocals upbeat fun guitar fiddle
- (English, planned) Piano, dramatic, melodic

### Cool Jazz
- (English, planned) The track opens with sultry, smoky sax lines over a subtle upright bass motif. A dynamic, multi-layered jazz percussion section enters, featuring congas, cymbals, and intricate snare work. Operatic vocal flourishes weave with the rhythm, building rich, dramatic crescendos.

### Country Gospel
- (English, direct) Classic Country, 1960s female vocal, storytelling, honky tonk, acoustic guitar, piano, fiddle, steel guitar, simple drums, warm analog production
- (English, direct) Upbeat gospel bluegrass style, male lead vocal, energetic and joyful, fast tempo, acoustic instrumentation with frequent instrumental solos including banjo, fiddle, mandolin, and acoustic guitar, upright bass driving rhythm, less drum, add harmonica and spoons, Appalachian revival feel, storytelling lyrics based on the King James Version Bible, martyrdom and gospel mission theme, strong harmony choruses, celebratory and foot-stomping

### Country Pop
- (English, direct) country
- (English, direct) Contemporary country, harmony

### Country Rock
- (English, direct) pop-rock hit,male vocals

### Cyber Metal
- (English, planned) energetic,Punk,Ambient,bass,合成器,EDM,Rhythmic sense,dreamy,symphony,saxophone,English
- (English, planned) Dark electronic rock with industrial beats and cinematic synths, heavy bass and distorted guitars, urgent male vocal with spoken-word intensity rising into melodic anthemic chorus, cyberpunk atmosphere, driving rhythm, dystopian but empowering tone. A powerful, prophetic anthem about The Matrix, the old Internet, and AI as a kernel patch. Driving beat, sharp lyrics, chorus hook: The red pill isn’t seeing — the red pill is to build.
- (English, planned) Alternative Metal song at 100 BPM with emotional and cinematic tone. Male lead vocal — expressive, powerful, and slightly gritty. Verses combine melodic rap and atmospheric spoken delivery; choruses are sung with intensity and emotional depth. The music blends heavy guitars, piano, electronic textures, and modern rock drums. The mood is dramatic, futuristic, and introspective — about the struggle and triumph within a digital world. Include a short guitar solo or synth break before the final chorus. Production should feel modern, cinematic, and slightly melancholic, with a sense of rising energy. Atmosphere: electricity, data storms, neon light, and human emotion inside the machine.
- (English, planned) At 148 BPM, the synthwave-trap fusion kicks in with thick analog bass, neon pads, thumping 808s, and sharp gated snares. Verses blend electric guitar, rapid hi-hats, and bubbling synths. Choruses burst with double-time trap beats, soaring retro synth leads, lush riffs, cinematic strings, swirling arps, water FX, and fluid transitions beneath dynamic vocals. Breakdowns spotlight vintage strings, wavesynth layers, double-kicks, deep sub-bass, and overdriven guitar, evoking a liquid-wave vibe. Trap DJ drops, pulsing melodic guitar, and remix-ready edits inject extra retro-modern punch.

### Dance-Pop
- (Chinese, planned) A groove-driven 124bpm pop, synth-pop, and funk fusion: pulsating synths and syncopated funk guitar ride over tight handclaps and a punchy, rhythmic bass. Fast, bright mid-low vocals lead, with sharp drums and synth stabs fueling the choruses. The bridge blends upbeat pop rock and soft rock elements, adding lush harmonies and airy synth layers, then surges back to an energetic, infectious finish.

### Dance-Punk
- (Japanese, planned) An explosive, high-energy J-pop and dance-pop track driven by a powerful four-on-the-floor electronic drum beat and a pulsing synth bassline. The arrangement opens with layered, atmospheric female vocal chops before launching into verses with a confident, rhythmic vocal delivery that mixes Japanese and English. The chorus erupts with soaring, belted vocals, layered harmonies, and bright, cutting synth leads. The track features a dynamic structure with rap-like sections, a more melodic and atmospheric bridge, and a powerful build-up leading to a final, anthemic chorus. The production is polished and modern, filled with synth arpeggios, risers, and vocal effects that maintain a constant sense of forward momentum.

### Dark Ambient
- (English, planned) Pop,Rock,Country,Medium,Anticipation,Triumph,Uplifting
- (English, planned) Orchestral-Electro Fusion with Augmented Tension Arcs, Cathedral Choir Swells, and Tempo-Morphing Cinematics, Soul music, gorgeous, dreamy, violin, violin, violin, violin, violin, violin, violin, violin, violin, violin, Mezzo-soprano female, Slow tempo, Well-defined rhythm

### Disco
- (Chinese, direct) City Pop, upbeat, funky bass, synth, electric guitar, neon city night, danceable

### Dixieland
- (English, planned) Electo-Swing

### Easy Listening
- (Japanese, planned) A gentle and melancholic piece beginning with a delicate piano melody and a breathy, expressive flute line. A soft, clear female vocal enters, singing in a gentle, almost lullaby-like style. The arrangement gradually builds, introducing a subtle, downtempo lo-fi hip-hop beat with a soft kick and snare, complemented by a warm bassline and atmospheric synth pads. The track maintains a tranquil and introspective mood throughout, with the piano and flute weaving in and out, creating a serene soundscape perfect for relaxation or contemplation. The song concludes with a beautiful instrumental outro featuring the piano and flute, fading into silence.

### Electronic Dance Music
- (Chinese, planned) Opening with pulsing bass oscillations over a four-on-the-floor kick, syncopated claps, and crisp hi-hats, the track builds as lush synth chords swell in, escalating tension, The drop explodes with thick bass modulation, chopped vocal hooks, and vibrant FX atop the relentless groove, Pop music, DJ, EDM, Heavy Metal, disco, happy, energetic, inspire, excited, Guitar, piano, percussion, bass, Electric guitar, Electric Piano, Pad, electronic drums, drum kit, heavy drums, sub-bass, keyboard, pop vocal, vibrato, room reverb, metallic vocal fx, delay/echo, intense, rhythmic, powerful, harmony

### Electropop
- (Chinese, planned) Dynamic, Pop Ballad, J-Pop, Pipa, Percussion, Electric Guitar, Conga, Sprung Rhythm, Driving Rhythm, Male Vocals, Mandarin
- (Chinese, direct) Chinese Pop,inspiring,upbeat,piano,guitar,training scene

### Emo
- (Korean, planned) A melancholic yet energetic Emo Hip-hop track with Pop Punk influences. Heavy distorted electric guitar riffs combined with fast-paced trap drum beats (808 bass, crisp snare). Dark, emotional, and cinematic atmosphere. Melodic Rap beat featuring a lonely acoustic guitar intro transitioning into an explosive chorus with heavy rock guitars. Deep, distorted 808 bass and sharp hi-hats. Sad, longing melody. Fast-paced Emo Rock and Hip-hop fusion. High-energy electric guitar loops, upbeat but sad melody, 140 BPM ~ 160 BPM, driving drum rhythm. A female vocal with a husky, raspy tone and heavy auto-tune. The singing style is emotional melodic rap. Add high reverb to create a lonely, atmospheric vibe. The voice should sound raw yet polished with metallic pitch correction.

### Emo-Pop
- (English, direct) teen pop genre, emotional, female vocals, synth-pop production, heartbreak, angsty

### Enka
- (Japanese, direct) retro,city pop,中森明菜,Japanese

### Ethio-Jazz
- (English, planned) An energetic and swinging big band jazz arrangement kicks off with a lively saxophone fanfare over a walking upright bass and crisp ride cymbal. A charismatic male crooner delivers the lead vocal with a smooth, expressive tone, supported by a full horn section of saxophones and brass that punctuates the track with powerful stabs and counter-melodies. The rhythm section, featuring piano, bass, and drums, maintains an infectious, upbeat swing groove throughout. The song includes dynamic instrumental breaks with spirited saxophone solos and a brief, spoken-word section in English towards the end, adding a unique texture before a final, powerful chorus and a saxophone-led outro.

### Eurobeat
- (English, planned) Dance, Eurobeat, cute, J-Pop Style, EDM Style, male vocal
- (Japanese, direct) An energetic J-pop track with strong Eurobeat and trance influences. The song opens with a brief atmospheric soundscape before launching into a driving four-on-the-floor drum machine beat and a pulsing synth bassline. Bright, arpeggiated synthesizers and a prominent piano melody carry the main theme. The clear, emotional male lead vocal delivers a passionate performance, soaring over the dense electronic arrangement. The structure features dynamic builds into powerful choruses, a brief instrumental break with layered synths, and a more reflective bridge section that momentarily pulls back the intensity before a final, climactic chorus and an instrumental fade-out.

### Flamenco
- (Spanish, planned) flamenco gipsy female vocals, deep male spanish rap voice, hip hop beat with cajón and bass, flamenco guitar, palmas, 95 bpm, joyful energy, andalusian accent, fusion, bright tone, no melancholy, festive rhythm, call and response vocals, uplifting and emotional, warm analog texture, street spirit, modern flamenco rap fusion, mediterranean vibe, vibrant and organic production.
- (Japanese, planned) jazz manouche, super hasky voice, middle tempo

### Folktronica
- (Russian, planned) Dance Pop, Storytelling, Groovy, Anthemic, Dance, Folk, Melodic, Danceable, Electronic, female vocals

### Funk
- (Chinese, direct) Disco, ballad pop, gentle rhythm, comfortable, fast pace, electric piano, bass, pad, 808, percussion, male vocals, Mandarin.

### Funk Rock
- (Chinese, planned) Strange,Funk,DJ,EDM,j-pop,rock,saxophone,Electric guitar,Rhythmic sense,Strong rhythm,120bmp,Male Vocals,Mandarin
- (Chinese, planned) happy,disco,Electric guitar,Guitar,bass,percussion,Synthesizer,Strong rhythm,Rhythmic sense,Powerful rhythm,Male Vocals,Mandarin
- (Chinese, direct) Comedy Rock, Satirical Mood, Electric Guitar & Synth Brass, Corporate Restroom Absurdity with Disco Funk Grooves

### Glam Metal
- (English, planned) 1980s pop, classic rock
- (English, direct) modern rock, 80s rock, Springsteen-inspired, anthemic, piano, saxophone, heartfelt, nostalgic, cinematic rock
- (English, direct) aor classic rock, arena rock, 80's, male singer, Background vocals, catchy

### Grime
- (English, planned) UK pop rap, melodic rap, R&B hook, rap‐sung chorus, trio vocals, call‐and‐response, catchy chant hook, ad‐lib heavy, autotune accents, emotional storytelling, nostalgic 90s UK, grime‐pop fusion, UK garage bounce, 2‐step groove, club anthem, radio‐ready polish, stacked harmonies, urban strings, piano stabs, synth stabs, punchy claps and 808s, minor‐key drama, halftime bridge switch, 130‐140 BPM, youthful street energy, anthemic crowd vocals

### Heartland Rock
- (English, planned) melodic, bright, classic, electric guitars, rock, classic 80s rock

### Hi-NRG
- (English, planned) SUPER EUROBEAT, J-Heavymetal, J-Eurobeat, Anime opening, J-Eurobeat very fast-paced with eurobeat riffs, catchy funky extreme japanese eurobeat, Bass pattern, Synthersized

### Honky Tonk
- (English, direct) Duet, Good time country, dance music, honky tonk

### Indie Rock
- (Chinese, planned) Pop music, Funk, rock, happy, energetic, excited, Guitar, percussion, bass, Electric guitar, rhythmic, bouncing, intense

### Industrial Hip Hop
- (English, planned) EDM, Metal, Hip Hop, Male Vocals, Harmonized Vocals, Growling, Rap Vocals, Cinematic, Aggressive, Bass, Electric Guitar, Rhythm Guitar, Drums, Keyboard, Synth, build a dystopian heavy metal trap beat with EDM elements and over the top excitement filling the voids with echoes and haunting house

### Industrial Metal
- (Chinese, planned) powerful belting, autotune, Electric guitar, symphony, bass, Electric Piano, excited, bold, Heavy Metal
- (Chinese, planned) Genre: Cyber Epic Core / Industrial Reverb Bass. Core Tone: The ultimate clash between cold machinery and burning humanity, blending a grand narrative with the raw impact of an underground fight. Rhythm & Groove - Tempo: 155 BPM. Time Signature: 4/4, emphasizing mechanical syncopation on the backbeat. Groove Core: An industrial, precision kick drum forms the skeleton, layered with the wild accents of distorted Electric guitar, creating an auditory collision of "precise calculation" and "savage impact." Instrument Timbres - Percussion: Hardcore Kick layered with metal percussion samples (sounds of robotic arms operating, guns cocking). Bass: Reverb Bass (Wobble Bass) and sub-bass synths generating an earth-shaking sense of oppression. Melodic Layer: A Wall of Sound from distorted Electric guitar and piercing synth Leads (simulating alarms and data streams). Atmosphere Layer: A Dark Choir pad underneath, interspersed with glass breaking, static noise, and other Glitch effects. Emotional

### Italo-Disco
- (English, planned) dance, female vocals

### J-Pop
- (Chinese, planned) A quintessential 90s Japanese anime OP, this track blends J-pop with Japanese pop rock at around 100 BPM, driven by bright distorted guitars and upbeat drums. The passionate vocal melody and rhythm-packed, youthful chorus brim with hope and adventure, capturing the vibrant energy of classic Japanese animation.
- (English, planned) A polished J-Pop and R&B track built on a crisp, modern drum machine beat and a smooth, rounded synth bassline. The arrangement features clean, melodic synth leads and atmospheric pads that create a bright, romantic soundscape. A male vocalist delivers a confident performance, seamlessly switching between rhythmic rapping in the verses and smooth, sung melodies in the catchy chorus. The vocals are layered with harmonized backing tracks and punctuated by echoed ad-libs, enhancing the track's dynamic and full-bodied feel. The song follows a classic pop structure with a reflective bridge that momentarily softens the energy before a final, emphatic chorus and a fading synth-led outro.

### Jazz-Funk
- (Japanese, planned) funk

### Jazz-Rock
- (Japanese, direct) rock,jazz,Strong rhythm,Powerful rhythm,Rhythmic sense,Guitar,piano,Electric guitar,percussion,saxophone,cello,violin,bass,女高音,激情,Fast pace,R&B,Japanese

### Jump Blues
- (English, planned) Swinging 160 BPM jump blues, honking sax section, walking upright slap, boogie-woogie piano, shiny archtop chops, brass punches, crowd-shout hooks, dance-floor fire.

### Lo-Fi Hip Hop
- (Chinese, direct) R&B, upbeat, romantic, sweet vibe, synth, bass, rap, first-person crush
- (Chinese, direct) Epic,ballad pop,R&B,piano,Guitar,Pipa,percussion,Electric Piano,Electric guitar,808,cello,violin,bass,弱起,推情绪,桥段琶音给情绪,Rhythmic sense,Gentle rhythm,Male Vocals,Mandarin

### Metal
- (Japanese, planned) An explosive J-Rock track driven by high-energy, technical instrumentation. The song opens with a blistering, shred-style guitar solo featuring rapid-fire licks and whammy bar flourishes over a powerful, driving drum beat. A clear, powerful female vocal enters, delivering an emotional and soaring melody typical of the Anisong genre. The arrangement is dense, built on layers of distorted rhythm guitars, a punchy bassline, and dynamic, fill-heavy drumming. The choruses are anthemic and expansive, with the vocals reaching a higher register. The track features multiple intricate guitar solos and a brief, softer bridge that builds tension before launching back into the final powerful chorus and a technical guitar-focused outro.

### Nu-Disco
- (Chinese, planned) City Pop, upbeat, danceable, groovy bass, electric guitar, synth, energetic, joyful, neon city night

### Pop Rock
- (Chinese, direct) An energetic pop-rock anthem kicks off with a clean, arpeggiated electric guitar figure before launching into a driving, full-band arrangement. The track is propelled by a punchy acoustic drum kit and a solid, foundational bassline. Overdriven power-chord guitars provide a crunchy, powerful texture throughout. A clear, youthful male lead vocal delivers an optimistic and anthemic melody, reinforced by layered backing vocals in the soaring chorus. The structure includes a brief, melodic guitar break and a dynamic bridge that momentarily softens before rebuilding into a final, powerful chorus and a guitar-led outro that fades out.

### R&B
- (Chinese, planned) Modern Chinese pop R&B with synth-pop influence, emotional and intimate atmosphere, Intro starts with a clear and emotional lead synth melody, simple and memorable, soft and slightly fragile, close-mic, expressive and melodic, Clean pop drum groove, tight punchy kick, natural snare with soft room reverb, minimal hi-hat pattern, smooth R&B bounce, Warm melodic synth bass with smooth movement, Analog-style synths with slight detune, warm tone, gentle filter movement, soft low-pass, subtle chorus width, Lead synth is smooth and rounded, emotional and expressive, High-frequency bell-like pluck synth in the background, soft and bright, short notes with light delay and reverb, adding sparkle and rhythmic detail, Wide atmospheric pads with slow attack and breathing movement, Minimal and clean arrangement, layered but spacious, focusing on melody and texture, Wide stereo image, airy reverb and delay, polished and warm, Pop music, Well-defined rhythm , Well-defined rhythm

### Rap Metal
- (Chinese, direct) Chinese Epic Rock, Power Metal, Shaanxi Opera, Dramatic, Energetic, Viral, National Trend (中国风史诗摇滚,力量金属,秦腔,戏剧性,充满活力,病毒式传播,国潮)

### Reggaetón
- (English, direct) slow, reggaeton, just configs, str22ipped-back reggaeton, 222 bpm, and our182 voices trading verses, soft, hand the heartbeats

### Rock & Roll
- (English, planned) Joyful happy 50s male powerful

### Soft Rock
- (Chinese, direct) energetic,ballad pop,Guitar,piano,Rhythmic sense,Male Vocals,Mandarin
- (Chinese, direct) Light Pop

### Soul
- (Chinese, planned) R&B,happy,ballad pop,Chinese Traditional Folk,jazz,EDM,percussion,saxophone,Electric guitar,Rhythmic sense,Male Vocals
- (Chinese, direct) Emotion,ballad pop,R&B,jazz,piano,saxophone,Powerful rhythm,Strong rhythm,Rhythmic sense,Mandarin

### Soul Blues
- (English, planned) Soul-blues, 12-takt smooth, electric guitar, hammondorgel, drums, groovy bass, emotionell, blues inspirered soulful male ande female song
- (English, planned) ballad, Blues

### Southern Gospel
- (English, planned) Medium tempo Southern Gospel , fast violin, mandolin, steel guitar, harmonica
- (English, direct) upbeat Christian country song, medium beat, acoustic guitar, add fiddle, joyful male harmonies

### Southern Soul
- (English, planned) Southern Soul, R&B, Grand Piano, Saxophone, Background Vocals, Jazz Fusion, Uplifting, Peaceful, Playful, Dreamy, Soulful and Lively, Atmosphere, Romantic danceable, seductive, emotional, Male voice, medium, changing Tempo Steady, Accelerating, Decelerating, night-lovingscene, Atmospheric, soulful, ear cany, Anticipation, surprise

### Space Rock
- (English, direct) Melodic Hard Rock:1.4), (AOR:1.3), (80s Arena Rock Revival). BPM: 124. Vibe: Uplifting, Romantic, Energetic, Polish. Instruments: Bright analog synthesizer hooks (Oberheim style), driving palm-muted electric guitars, melodic bassline, massive snare with gated reverb. Vocals: Male, High Tenor, clean tone with moments of grit, passionate and soaring delivery. Features: [Catchy Keyboard Intro], [Power Chord Progressions], [Layered Vocal Harmonies in Chorus], [Melodic Shred Guitar Solo]. Structure: Intro, Verse, Pre-Chorus, Explosive Chorus, Verse, Bridge, Solo, Final Chorus, Outro. Production: Crystal clear, studio quality.

### Swing
- (Chinese, planned) Genre: Jazz-Pop,Swing,Comedy Music Style: Whimsical,playful,upbeat,vintage,comedic,reminiscent of a silent film era soundtrack,with a touch of musical theater. Similar to the playful energy of "Mr. Sandman" by The Chordettes or the style of "特大号鞋子". Instrumentation: Upright bass (slap bass),light and crisp drums (brush strokes),playful piano,trumpet stabs,clarinet,xylophone,sound effects (slide whistle,bicycle horn,quirky footsteps). Structure: The song follows a clear structure: [Verse 1] [Pre-Chorus] [Chorus] [Verse 2] [Bridge] [Chorus] [Outro]. Description: A male vocalist with a charismatic,smiling,and slightly theatrical voice,half-singing half-speaking the lyrics with a lot of character and playful exaggeration. The mood is lighthearted,humorous,and rebellious against boredom through absurdity. The tempo is upbeat and bouncy.

### Swing Revival
- (English, planned) A lively swing number bursts in with a bold brass section and playful saxophone riffs over a walking upright bass. Syncopated drums drive the rhythm, inviting dancing. Cheerful horn stabs and energetic call-and-response jams keep the mood loose and celebratory throughout., electronic, synth, aggressive
- (English, planned) funk, Hyperactive jazz-pop meets Brazilian funk groove with mento bounce and a crooked dark-cabaret piano. Bright brass stabs, rubbery bass, and clattering percussion keep everything rushing forward; verses stay frantic and playful, chorus hooks explode with gang vocals and call‐and‐response. Male vocals, sly and theatrical, with stacked harmonies on the hook and a brief half‐time breakdown before the final chorus., jazz, dark cabaret, pop

### Thrash Metal
- (English, direct) 重金属,华丽,,guitar solo,黑暗,阴险,激流金属,,男声

### Yacht Rock
- (Japanese, direct) Vintage Motown Soul Duet, Romantic, Smooth, Soulful Female Vocal and Tender Male Vocal, Lush Orchestral Strings, Wah-Wah Electric Guitar Riff, Upright Bass and Light Percussion, about mutual devotion and being each other's world, Medium Tempo.

## 5. 官方翻唱/改编演示

官方另有改编演示（换词、换风格等），仅列出类型供参考，原曲歌词不收录。

| 标题 | 曲风 | 改编类型 |
|---|---|---|
| Jingle Bells · Minor-Key Version | Christmas Pop · E Minor · 104 BPM | Melody remapping: G major → E natural minor · Chordless melody input |
| Where Is My Wallet | Theatrical Hard Rock · 176 BPM | Lyric rewrite · Structural excerpt · Chord-conditioned ABC |
| Auld Lang Syne · Jazz-Funk Version | Soulful Jazz-Funk · 104 BPM | Tempo change: 82 → 104 BPM · Chordless melody input · Style rearrangement |
| Jingle Bells · Heavy-Metal Version | Heavy Metal Rock · 160 BPM | Tempo change: 104 → 160 BPM · Chordless melody input · Style rearrangement |
| Where Is Spring? · Minor-Key Version | Chamber Folk · D Minor · 118 BPM | Melody remapping: F major → D natural minor · Chordless melody input |
| Big Pineapple | Tropical Calypso-Pop · 122 BPM | Lyric rewrite · Style rearrangement · Chord-conditioned ABC |
| Big Dog Goes Woof | New Orleans Brass-Funk · 115 BPM | Lyric rewrite · Style rearrangement · Chord-conditioned ABC |
| Happy Birthday · Heavy-Metal Scream Version | Heavy Metal · 160 BPM | Tempo change: 97 → 160 BPM · Style rearrangement |
| Lake Baikal · Chinese Jazz Version | Jazz Ballad · 60 BPM | Style rearrangement |
| The Most Dazzling Folk Style · Compact Ballad Version | Intimate Piano Ballad | Structural reduction · Tempo change: 126 → 90 BPM · Style rearrangement |
| Interstellar | Electronic Metal |  |

其中 Interstellar 是纯器乐改编（无人声），官方没有公开它的 prompt 和乐谱。
