"""Pasted subtitles (plain lines, SRT, LRC) become tagged lyrics; tagged lyrics stay as they are."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
from studio import flow  # noqa: E402

plain = "第一行歌词\n第二行歌词\n\n第三行歌词\n"
srt = "1\n00:00:01,000 --> 00:00:03,500\n第一行歌词\n\n2\n00:00:03,500 --> 00:00:06,000\n第二行歌词\n"
lrc = "[00:01.00]第一行歌词\n[00:03.50]第二行歌词\n[00:06.00]"
tagged = "[Verse]\n第一行歌词\n\n[Chorus]\n第二行歌词"
english = "1\n00:00:01,000 --> 00:00:02,000\nWalking home tonight\n"

assert flow.normalize_lyrics(plain) == "[Verse]\n第一行歌词\n第二行歌词\n第三行歌词", flow.normalize_lyrics(plain)
assert flow.normalize_lyrics(srt) == "[Verse]\n第一行歌词\n第二行歌词", flow.normalize_lyrics(srt)
assert flow.normalize_lyrics(lrc) == "[Verse]\n第一行歌词\n第二行歌词", flow.normalize_lyrics(lrc)
assert flow.normalize_lyrics(tagged) == tagged
assert flow.normalize_lyrics(english) == "[Verse]\nWalking home tonight"
assert flow.normalize_lyrics("") == "" and flow.normalize_lyrics(None) is None
# numbers inside real lyric lines are kept
assert "2046" in flow.normalize_lyrics("我们在2046相遇")
print("normalize_lyrics OK")
