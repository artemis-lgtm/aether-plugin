#!/usr/bin/env python3
"""
V4: Wood texture, RED neon (not pink), MUCH bigger title, portrait with red neon.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math, os

random.seed(42)

skin = Image.open("/tmp/aether-art/dalle-wood/001-hyper-realistic-top-down-photograph-of-a.png")
W, H = 1020, 620

# Stretch to fill completely
skin = skin.resize((W, H), Image.LANCZOS)
img = skin.copy().convert("RGBA")

# Edge-extend to prevent any black at UV boundaries
for x in range(W):
    c = img.getpixel((x, 3)); [img.putpixel((x, y), c) for y in range(3)]
    c = img.getpixel((x, H-4)); [img.putpixel((x, y), c) for y in range(H-3, H)]
for y in range(H):
    c = img.getpixel((5, y)); [img.putpixel((x, y), c) for x in range(5)]
    c = img.getpixel((W-6, y)); [img.putpixel((x, y), c) for x in range(W-5, W)]

# ============================================================
# FONTS
# ============================================================
ff = None
for fp in ["/System/Library/Fonts/Supplemental/MarkerFelt.ttc",
           "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"]:
    if os.path.exists(fp): ff = fp; break
if not ff: ff = "/System/Library/Fonts/Helvetica.ttc"

title_font_big = ImageFont.truetype(ff, 48)  # MUCH BIGGER
sect_font = ImageFont.truetype(ff, 19)
label_font = ImageFont.truetype(ff, 13)

# ============================================================
# RED NEON COLOR
# ============================================================
NEON_RED = (255, 40, 40)

# ============================================================
# HELPERS
# ============================================================
def make_tape(w, h, color=(222, 210, 180), alpha=215):
    tape = Image.new("RGBA", (w + 6, h + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(tape)
    d.rectangle([3, 3, w + 2, h + 2], fill=(*color, alpha))
    for _ in range(4):
        y2 = random.randint(3, h + 1)
        v = random.randint(-12, 12)
        c = tuple(max(0, min(255, cc + v)) for cc in color)
        d.rectangle([3, y2, w + 2, y2 + random.randint(1, 2)], fill=(*c, alpha - 15))
    for x in range(w + 6):
        for dy in range(3):
            if random.random() < 0.4: tape.putpixel((x, dy), (0,0,0,0))
            if random.random() < 0.4: tape.putpixel((x, h+5-dy), (0,0,0,0))
    for y2 in range(h + 6):
        for dx in range(2):
            if random.random() < 0.5: tape.putpixel((dx, y2), (0,0,0,0))
            if random.random() < 0.5: tape.putpixel((w+5-dx, y2), (0,0,0,0))
    return tape

def paste_tape(img, tape, x, y, angle=0):
    if angle: tape = tape.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(tape, (x, y), tape)

def sharpie(img, text, x, y, font, color=(220, 215, 200), center=False):
    d = ImageDraw.Draw(img)
    if center:
        bb = d.textbbox((0,0), text, font=font)
        x = x - (bb[2] - bb[0]) // 2
    for dx, dy in [(-1,0),(1,0),(0,-1)]:
        d.text((x+dx, y+dy), text, fill=(*color, 35), font=font)
    d.text((x, y), text, fill=(*color, 255), font=font)

def neon_border(img, x, y, w, h, color=NEON_RED, glow_radius=12, thickness=3):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(glow_radius, 0, -1):
        alpha = int(90 * (1 - r / glow_radius))
        gd.rectangle([x-r, y-r, x+w+r, y+h+r], outline=(*color, alpha), width=2)
    gd.rectangle([x, y, x+w, y+h], outline=(*color, 255), width=thickness)
    inner = (min(255,color[0]+60), min(255,color[1]+100), min(255,color[2]+100))
    gd.rectangle([x+1, y+1, x+w-1, y+h-1], outline=(*inner, 160), width=1)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=5))
    gd2 = ImageDraw.Draw(glow)
    gd2.rectangle([x, y, x+w, y+h], outline=(*color, 245), width=thickness)
    gd2.rectangle([x+1, y+1, x+w-1, y+h-1], outline=(*inner, 130), width=1)
    return Image.alpha_composite(img, glow)

def neon_text(img, text, x, y, font, color=NEON_RED, center=False):
    d = ImageDraw.Draw(img)
    if center:
        bb = d.textbbox((0,0), text, font=font)
        x = x - (bb[2] - bb[0]) // 2
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for dx2 in range(-4, 5):
        for dy2 in range(-4, 5):
            dist = math.sqrt(dx2*dx2 + dy2*dy2)
            if dist <= 4:
                alpha = int(70 * (1 - dist / 4))
                gd.text((x+dx2, y+dy2), text, fill=(*color, alpha), font=font)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=4))
    gd2 = ImageDraw.Draw(glow)
    inner = (255, min(255,color[1]+120), min(255,color[2]+120))
    gd2.text((x, y), text, fill=(*inner, 255), font=font)
    return Image.alpha_composite(img, glow)

# ============================================================
# TITLE - MUCH BIGGER with red neon
# ============================================================
title_text = "Austin's Secret Sauce"
# Dark backing
draw = ImageDraw.Draw(img)
bb = draw.textbbox((0,0), title_text, font=title_font_big)
tw = bb[2] - bb[0]
th = bb[3] - bb[1]
pad_x, pad_y = 30, 14
box_w = tw + pad_x * 2
box_h = th + pad_y * 2
bx = (W - box_w) // 2
by = 10

# Semi-transparent dark backing
backing = Image.new("RGBA", (box_w, box_h), (30, 25, 20, 200))
img.paste(backing, (bx, by), backing)

# Red neon border
img = neon_border(img, bx, by, box_w, box_h, color=NEON_RED, glow_radius=14, thickness=4)

# Red neon text
img = neon_text(img, title_text, bx + box_w // 2, by + pad_y - 2, title_font_big, color=NEON_RED, center=True)

# ============================================================
# SECTION HEADERS on masking tape
# ============================================================
sections = [
    ("SWELL",   40,  185,  220),
    ("VINYL",   40,  300,  160),
    ("MASTER",  40,  415,  160),
    ("PSYCHE",  385, 185,  490),
    ("LFO",     415, 358,  240),
]
for name, sx, sy, sw in sections:
    tape = make_tape(sw, 24)
    paste_tape(img, tape, sx, sy, angle=random.uniform(-1.5, 1.5))
    sharpie(img, name, sx + sw // 2, sy + 3, sect_font, color=(40, 35, 30), center=True)

# ============================================================
# KNOB LABELS
# ============================================================
knob_data = [
    ('Sens', 80, 240), ('Attack', 160, 240), ('Depth', 240, 240),
    ('Year', 80, 355), ('Detune', 160, 355),
    ('Mix', 80, 465), ('Gain', 160, 465),
    ('Shimmer', 420, 240), ('Space', 490, 240), ('Mod', 560, 240),
    ('Warp', 630, 240), ('Mix', 700, 240), ('Notch', 770, 240), ('Sweep', 840, 240),
    ('Shape', 455, 410), ('Rate', 535, 410), ('Depth', 615, 410),
    ('Div', 455, 485), ('Phase', 535, 485),
]
KNOB_R_UV = 32

for name, kx, ky in knob_data:
    lw = max(45, len(name) * 8 + 14)
    lh = 16
    tape = make_tape(lw, lh, color=(228, 218, 190))
    ly = ky + KNOB_R_UV + 5
    lx = kx - lw // 2
    paste_tape(img, tape, lx, ly, angle=random.uniform(-2, 2))
    sharpie(img, name, kx, ly + 2, label_font, color=(40, 35, 30), center=True)

# SYNC
sync_tape = make_tape(55, 20, color=(215, 205, 175))
paste_tape(img, sync_tape, 700, 445, angle=random.uniform(-1, 1))
sharpie(img, "SYNC", 727, 448, label_font, color=(40, 35, 30), center=True)

# ============================================================
# AUSTIN'S PORTRAIT with RED neon frame
# ============================================================
portrait_path = "/tmp/aether-art/austin-portrait-square.jpg"
if os.path.exists(portrait_path):
    portrait = Image.open(portrait_path).convert("RGBA")
    pw, ph = 175, 175
    portrait = portrait.resize((pw, ph), Image.LANCZOS)
    px = W - pw - 35
    py = H - ph - 40
    img.paste(portrait, (px, py), portrait)
    img = neon_border(img, px - 6, py - 6, pw + 12, ph + 12,
                       color=NEON_RED, glow_radius=14, thickness=4)

# ============================================================
# SCRATCHES
# ============================================================
scratch = Image.new("RGBA", (W, H), (0,0,0,0))
sd = ImageDraw.Draw(scratch)
for _ in range(45):
    x1 = random.randint(0, W); y1 = random.randint(0, H)
    l = random.randint(30, 160); a = random.uniform(0, math.pi)
    x2 = x1 + int(l*math.cos(a)); y2 = y1 + int(l*math.sin(a))
    sd.line([(x1,y1),(x2,y2)], fill=(180,165,140,random.randint(20,50)), width=1)
img = Image.alpha_composite(img, scratch)

out = "/tmp/aether-art/dalle_face_v4.png"
img.convert("RGB").save(out, quality=95)
print(f"Saved: {out} ({W}x{H})")
