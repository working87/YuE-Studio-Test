"""Draw the app icon (orange rounded square with a white eighth note)."""
from pathlib import Path

from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((8, 8, S - 8, S - 8), radius=56, fill=(217, 72, 15, 255))
white = (255, 255, 255, 255)
d.ellipse((58, 150, 128, 206), fill=white)          # note head
d.rectangle((114, 52, 130, 180), fill=white)        # stem
d.polygon([(130, 52), (196, 86), (196, 118), (130, 86)], fill=white)  # flag
out = Path(__file__).resolve().parents[1] / "build" / "icon.ico"
out.parent.mkdir(exist_ok=True)
img.save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(out)
