#!/usr/bin/env python3
"""Generate the social images (1200x630) from the current palette:
assets/og-image.png (hub, kept for older links) and one image per page
under assets/og/ (hub, cv, products, blog, lab, ai, academy).
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

def font(bold, size):
    for p in ([ "/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else ["/System/Library/Fonts/Supplemental/Arial.ttf"]) + ["/System/Library/Fonts/Helvetica.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except OSError: pass
    return ImageFont.load_default(size=size)

def portrait(size, radius):
    p = Image.open(os.path.join(ROOT, "assets/janaka2.jpg")).convert("RGB")
    side = min(p.size)
    p = p.crop(((p.width - side)//2, 0, (p.width - side)//2 + side, side)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return p, mask

def hub_image():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((80, 150, 156, 156), radius=3, fill=AC)          # accent rule
    d.text((80, 186), "Janaka", font=font(True, 68), fill=TX)
    d.text((80, 256), "Premathilaka", font=font(True, 68), fill=TX)
    d.text((80, 352), "Senior Java Engineer &", font=font(False, 30), fill=TX)
    d.text((80, 390), "Solution Architect", font=font(False, 30), fill=TX)
    d.text((80, 456), "Banking-grade Java · practical AI", font=font(False, 24), fill=TX2)
    d.text((80, 488), "in regulated systems · Zug", font=font(False, 24), fill=TX2)
    d.text((80, 560), "janaka.me", font=font(True, 24), fill=AC)
    p, mask = portrait(380, 28)
    im.paste(p, (740, 125), mask)
    return im

def page_image(eyebrow, lines, sub=None, url="janaka.me"):
    """Same family as the hub: dark ground, accent rule, eyebrow in the accent
    colour, headline, optional small line; a small portrait plus the 'J.'
    wordmark on the right so the page images stay distinct from the hub."""
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((80, 150, 156, 156), radius=3, fill=AC)
    d.text((80, 180), eyebrow.upper(), font=font(True, 26), fill=AC)
    y = 232
    for ln in lines:
        d.text((80, y), ln, font=font(True, 52), fill=TX); y += 62
    if sub:
        d.text((80, y + 18), sub, font=font(False, 24), fill=TX2); y += 40
    d.text((80, 520), "Janaka Premathilaka · Senior Java Engineer & Solution Architect", font=font(False, 22), fill=TX2)
    d.text((80, 560), url, font=font(True, 24), fill=AC)
    # right side: "J." wordmark on a card, small portrait beneath
    d.rounded_rectangle((900, 130, 1120, 300), radius=28, fill=BG2)
    d.text((940, 152), "J", font=font(True, 120), fill=TX)
    d.text((1020, 152), ".", font=font(True, 120), fill=AC)
    p, mask = portrait(180, 20)
    im.paste(p, (940, 330), mask)
    return im

PAGES = {
    "hub": None,
    "cv": ("CV", ["Two decades of", "critical systems."], None, "janaka.me/cv/"),
    "products": ("Products", ["Finished software,", "ready for a new owner."], "nüchtern · Daily Momentum · Loop · BabyLoop", "janaka.me/products/"),
    "blog": ("Blog", ["Clear, hands-on articles on", "Java, Kafka, RAG and agents."], None, "janaka.me/blog/"),
    "lab": ("Lab", ["Experiments and demos,", "with notes."], None, "janaka.me/lab/"),
    "ai": ("AI", ["Agents that are readable,", "reliable and worth shipping."], None, "janaka.me/ai/"),
    "academy": ("Academy", ["Engineers who surpass", "their teacher."], None, "janaka.me/academy/"),
}

def save(im, rel):
    out = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, optimize=True)
    print("wrote", rel, os.path.getsize(out)//1024, "KB")

hub = hub_image()
save(hub, "assets/og-image.png")
save(hub, "assets/og/hub.png")
for name, spec in PAGES.items():
    if spec:
        save(page_image(*spec), "assets/og/%s.png" % name)
