#!/usr/bin/env python3
"""
Create the face art texture at 1020x620 for Blender UV mapping.
DALL-E artwork + masking tape labels. No knob placeholders (Blender renders those).
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math, os

random.seed(42)

skin = Image.open("/tmp/aether-art/dalle-skins/001-hyper-realistic-photograph-of-a-vintage-.png")
W, H = 1020, 620

# Crop/resize to 1020x620
sr = skin.width / skin.height
tr = W / H
if sr > tr:
    nh = skin.height; nw = int(nh * tr)
    l = (skin.width - nw) // 2
    skin = skin.crop((l, 0, l + nw, nh))
else:
    nw = skin.width; nh = int(nw / tr)
    t = (skin.height - nh) // 2
    skin = skin.crop((0, t, nw, t + nh))
skin = skin.resize((W, H), Image.LANCZOS)
img = skin.copy().convert("RGBA")

# Fonts
font_paths = [
    "/System/Library/Fonts/Supplemental/MarkerFelt.ttc",
    "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
]
ff = None
for fp in font_paths:
    if os.path.exists(fp):
        ff = fp; break
if not ff:
    ff = "/System/Library/Fonts/Helvetica.ttc"

title_font = ImageFont.truetype(ff, 30)
sect_font = ImageFont.truetype(ff, 19)
label_font = ImageFont.truetype(ff, 13)

def make_tape(w, h, color=(222, 210, 180), alpha=215):
    tape = Image.new("RGBA", (w + 6, h + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(tape)
    d.rectangle([3, 3, w + 2, h + 2], fill=(*color, alpha))
    for _ in range(4):
        y = random.randint(3, h + 1)
        v = random.randint(-12, 12)
        c = tuple(max(0, min(255, cc + v)) for cc in color)
        d.rectangle([3, y, w + 2, y + random.randint(1, 2)], fill=(*c, alpha - 15))
    for x in range(w + 6):
        for dy in range(3):
            if random.random() < 0.4: tape.putpixel((x, dy), (0,0,0,0))
            if random.random() < 0.4: tape.putpixel((x, h+5-dy), (0,0,0,0))
    for y in range(h + 6):
        for dx in range(2):
            if random.random() < 0.5: tape.putpixel((dx, y), (0,0,0,0))
            if random.random() < 0.5: tape.putpixel((w+5-dx, y), (0,0,0,0))
    d.line([(3, h+3), (w+3, h+3)], fill=(30,25,20,35), width=1)
    d.line([(w+3, 3), (w+3, h+3)], fill=(30,25,20,35), width=1)
    return tape

def make_gaffer(w, h):
    return make_tape(w, h, color=(55, 52, 48), alpha=230)

def paste_tape(img, tape, x, y, angle=0):
    if angle: tape = tape.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(tape, (x, y), tape)

def sharpie(img, text, x, y, font, color=(30, 28, 25), center=False):
    d = ImageDraw.Draw(img)
    if center:
        bb = d.textbbox((0,0), text, font=font)
        x = x - (bb[2] - bb[0]) // 2
    for dx, dy in [(-1,0),(1,0),(0,-1)]:
        d.text((x+dx, y+dy), text, fill=(*color, 35), font=font)
    d.text((x, y), text, fill=(*color, 255), font=font)

# ============================================================
# Positions in native 1020x620 coordinates (from render_final.py)
# ============================================================
knob_data = [
    # (name, x, y)
    ('Sens', 80, 240), ('Attack', 160, 240), ('Depth', 240, 240),
    ('Year', 80, 355), ('Detune', 160, 355),
    ('Mix', 80, 465), ('Gain', 160, 465),
    ('Shimmer', 455, 240), ('Space', 535, 240), ('Mod', 615, 240), ('Warp', 695, 240),
    ('Mix', 455, 295), ('Notch', 535, 295), ('Sweep', 615, 295),
    ('Shape', 455, 410), ('Rate', 535, 410), ('Depth', 615, 410),
    ('Div', 455, 485), ('Phase', 535, 485),
]

# Section headers (name, x, y, tape_width)
sections = [
    ("SWELL",   40,  185,  220),
    ("VINYL",   40,  300,  160),
    ("MASTER",  40,  415,  160),
    ("PSYCHE",  415, 185,  310),
    ("LFO",     415, 358,  240),
]

# ============================================================
# TITLE on gaffer tape
# ============================================================
title_text = "Austin's Secret Sauce"
gw, gh = 400, 38
g = make_gaffer(gw, gh)
tx = (W - gw) // 2
ty = 25
paste_tape(img, g, tx, ty, angle=random.uniform(-0.5, 0.5))
sharpie(img, title_text, tx + gw // 2, ty + 6, title_font, color=(235, 230, 220), center=True)

# ============================================================
# SECTION HEADERS
# ============================================================
for name, sx, sy, sw in sections:
    tape = make_tape(sw, 24)
    paste_tape(img, tape, sx, sy, angle=random.uniform(-1.5, 1.5))
    sharpie(img, name, sx + sw // 2, sy + 3, sect_font, center=True)

# ============================================================
# KNOB LABELS (tape + sharpie, below each knob position)
# ============================================================
KNOB_R_UV = 32  # approximate knob radius in texture space

for name, kx, ky in knob_data:
    lw = max(50, len(name) * 9 + 16)
    lh = 17
    tape = make_tape(lw, lh, color=(228, 218, 190))
    ly = ky + KNOB_R_UV + 5
    lx = kx - lw // 2
    paste_tape(img, tape, lx, ly, angle=random.uniform(-2, 2))
    sharpie(img, name, kx, ly + 2, label_font, center=True)

# ============================================================
# SYNC label
# ============================================================
sync_tape = make_tape(55, 20, color=(215, 205, 175))
paste_tape(img, sync_tape, 700, 445, angle=random.uniform(-1, 1))
sharpie(img, "SYNC", 727, 448, label_font, center=True)

# ============================================================
# Bypass labels at bottom
# ============================================================
bypass = [("SWELL", 130), ("VINYL", 130), ("PSYCHE", 550), ("LFO", 550)]
by_y = 560
for name, bx in bypass:
    bt = make_tape(60, 16, color=(215, 205, 175))
    paste_tape(img, bt, bx - 30, by_y, angle=random.uniform(-1.5, 1.5))
    sharpie(img, name, bx, by_y + 2, label_font, center=True)

# ============================================================
# SCRATCHES
# ============================================================
scratch = Image.new("RGBA", (W, H), (0,0,0,0))
sd = ImageDraw.Draw(scratch)
for _ in range(40):
    x1 = random.randint(0, W); y1 = random.randint(0, H)
    l = random.randint(30, 160)
    a = random.uniform(0, math.pi)
    x2 = x1 + int(l * math.cos(a)); y2 = y1 + int(l * math.sin(a))
    sd.line([(x1,y1),(x2,y2)], fill=(210,200,185,random.randint(15,40)), width=1)
img = Image.alpha_composite(img, scratch)

out = "/tmp/aether-art/dalle_face_v1.png"
img.convert("RGB").save(out, quality=95)
print(f"Saved: {out} ({W}x{H})")
