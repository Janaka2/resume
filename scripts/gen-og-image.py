#!/usr/bin/env python3
"""Generate assets/og-image.png (1200x630) from the current palette.
Re-run after changing the design tokens in assets/css/theme.css."""
from PIL import Image, ImageDraw, ImageFont
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
css = open(os.path.join(ROOT, "assets/css/theme.css")).read()
dark = css[css.index('html[data-theme="dark"]'):]
def tok(name, block):
    return re.search(r"--%s:(#[0-9A-Fa-f]{6})" % name, block).group(1)
BG, BG2, TX, TX2, AC = (tok(n, dark) for n in ("bg", "bg2", "tx", "tx2", "ac"))

W, H = 1200, 630
im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)

def font(bold, size):
    for p in ([ "/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else ["/System/Library/Fonts/Supplemental/Arial.ttf"]) + ["/System/Library/Fonts/Helvetica.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except OSError: pass
    return ImageFont.load_default(size=size)

# accent rule
d.rounded_rectangle((80, 150, 156, 156), radius=3, fill=AC)
d.text((80, 186), "Janaka", font=font(True, 68), fill=TX)
d.text((80, 256), "Premathilaka", font=font(True, 68), fill=TX)
d.text((80, 352), "Senior Java Engineer &", font=font(False, 30), fill=TX)
d.text((80, 390), "Solution Architect", font=font(False, 30), fill=TX)
d.text((80, 456), "Banking-grade Java · practical AI", font=font(False, 24), fill=TX2)
d.text((80, 488), "in regulated systems · Zug", font=font(False, 24), fill=TX2)
d.text((80, 560), "janaka.me", font=font(True, 24), fill=AC)

# portrait, rounded square
p = Image.open(os.path.join(ROOT, "assets/janaka2.jpg")).convert("RGB")
side = min(p.size); p = p.crop(((p.width - side)//2, 0, (p.width - side)//2 + side, side)).resize((380, 380), Image.LANCZOS)
mask = Image.new("L", (380, 380), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 379, 379), radius=28, fill=255)
im.paste(p, (740, 125), mask)

out = os.path.join(ROOT, "assets/og-image.png")
im.save(out, optimize=True)
print("wrote", out, os.path.getsize(out)//1024, "KB")
