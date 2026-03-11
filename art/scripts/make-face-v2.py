#!/usr/bin/env python3
"""
V2 Face skin: DALL-E art stretched edge-to-edge, Psyche knobs in single row,
bigger title with pink neon border, Austin portrait with pink neon frame.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random, math, os
import numpy as np

random.seed(42)

# ============================================================
# LOAD DALL-E SKIN - stretch to fill 1020x620 completely
# ============================================================
skin = Image.open("/tmp/aether-art/dalle-skins/001-hyper-realistic-photograph-of-a-vintage-.png")
W, H = 1020, 620

# Stretch to fill entirely - slight overcrop to ensure no gaps
skin = skin.resize((W, H), Image.LANCZOS)
img = skin.copy().convert("RGBA")

# ============================================================
# FONTS
# ============================================================
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

title_font = ImageFont.truetype(ff, 36)
sect_font = ImageFont.truetype(ff, 19)
label_font = ImageFont.truetype(ff, 13)

# ============================================================
# HELPERS
# ============================================================
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

def neon_border(img, x, y, w, h, color=(255, 105, 180), glow_radius=8, thickness=3):
    """Draw a glowing neon border rectangle."""
    # Create glow layer
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    
    # Outer glow (multiple passes for bloom effect)
    for r in range(glow_radius, 0, -1):
        alpha = int(80 * (1 - r / glow_radius))
        expand = r
        gd.rectangle(
            [x - expand, y - expand, x + w + expand, y + h + expand],
            outline=(*color, alpha), width=2
        )
    
    # Core bright line
    gd.rectangle([x, y, x + w, y + h], outline=(*color, 255), width=thickness)
    
    # Inner glow (white-hot center)
    inner_color = (
        min(255, color[0] + 80),
        min(255, color[1] + 80), 
        min(255, color[2] + 80)
    )
    gd.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], outline=(*inner_color, 140), width=1)
    
    # Blur the glow layer
    glow = glow.filter(ImageFilter.GaussianBlur(radius=4))
    
    # Re-draw the sharp core on top of blur
    gd2 = ImageDraw.Draw(glow)
    gd2.rectangle([x, y, x + w, y + h], outline=(*color, 240), width=thickness)
    gd2.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], outline=(*inner_color, 120), width=1)
    
    img = Image.alpha_composite(img, glow)
    return img

def neon_text(img, text, x, y, font, color=(255, 105, 180), center=False):
    """Draw glowing neon text."""
    d = ImageDraw.Draw(img)
    if center:
        bb = d.textbbox((0,0), text, font=font)
        tw = bb[2] - bb[0]
        x = x - tw // 2
    
    # Glow layer
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    
    # Outer glow
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= 3:
                alpha = int(60 * (1 - dist / 3))
                gd.text((x + dx, y + dy), text, fill=(*color, alpha), font=font)
    
    glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
    
    # Sharp text on top
    gd2 = ImageDraw.Draw(glow)
    inner = (min(255, color[0]+60), min(255, color[1]+60), min(255, color[2]+60))
    gd2.text((x, y), text, fill=(*inner, 255), font=font)
    
    img = Image.alpha_composite(img, glow)
    return img

# ============================================================
# KNOB POSITIONS (updated: Psyche all 7 in one row)
# ============================================================
knob_data = [
    # LEFT COLUMN
    ('Sens', 80, 240), ('Attack', 160, 240), ('Depth', 240, 240),       # Swell
    ('Year', 80, 355), ('Detune', 160, 355),                             # Vinyl
    ('Mix', 80, 465), ('Gain', 160, 465),                                # Master
    # PSYCHE - ALL 7 IN ONE ROW (spaced across right section)
    ('Shimmer', 420, 240), ('Space', 490, 240), ('Mod', 560, 240), 
    ('Warp', 630, 240), ('Mix', 700, 240), ('Notch', 770, 240), ('Sweep', 840, 240),
    # LFO
    ('Shape', 455, 410), ('Rate', 535, 410), ('Depth', 615, 410),
    ('Div', 455, 485), ('Phase', 535, 485),
]

KNOB_R_UV = 32

# Section headers
sections = [
    ("SWELL",   40,  185,  220),
    ("VINYL",   40,  300,  160),
    ("MASTER",  40,  415,  160),
    ("PSYCHE",  385, 185,  490),
    ("LFO",     415, 358,  240),
]

# ============================================================
# TITLE - "Austin's Secret Sauce" - BIGGER with pink neon
# ============================================================
title_text = "Austin's Secret Sauce"

# Dark backing strip
gaffer_w = 480
gaffer_h = 50
gaffer = make_gaffer(gaffer_w, gaffer_h)
tx = (W - gaffer_w) // 2
ty = 15
paste_tape(img, gaffer, tx, ty, angle=0)

# Pink neon border around title
img = neon_border(img, tx, ty, gaffer_w, gaffer_h, color=(255, 105, 180), glow_radius=10, thickness=3)

# Neon text
img = neon_text(img, title_text, tx + gaffer_w // 2, ty + 8, title_font, color=(255, 105, 180), center=True)

# ============================================================
# SECTION HEADERS on masking tape
# ============================================================
for name, sx, sy, sw in sections:
    tape = make_tape(sw, 24)
    paste_tape(img, tape, sx, sy, angle=random.uniform(-1.5, 1.5))
    sharpie(img, name, sx + sw // 2, sy + 3, sect_font, center=True)

# ============================================================
# KNOB LABELS
# ============================================================
for name, kx, ky in knob_data:
    lw = max(45, len(name) * 8 + 14)
    lh = 16
    tape = make_tape(lw, lh, color=(228, 218, 190))
    ly = ky + KNOB_R_UV + 5
    lx = kx - lw // 2
    paste_tape(img, tape, lx, ly, angle=random.uniform(-2, 2))
    sharpie(img, name, kx, ly + 2, label_font, center=True)

# SYNC label
sync_tape = make_tape(55, 20, color=(215, 205, 175))
paste_tape(img, sync_tape, 700, 445, angle=random.uniform(-1, 1))
sharpie(img, "SYNC", 727, 448, label_font, center=True)

# ============================================================
# AUSTIN'S PORTRAIT with pink neon frame
# ============================================================
portrait_path = "/tmp/aether-art/austin-portrait-square.jpg"
if os.path.exists(portrait_path):
    portrait = Image.open(portrait_path).convert("RGBA")
    # Size it nicely for bottom-right
    pw, ph = 130, 130
    portrait = portrait.resize((pw, ph), Image.LANCZOS)
    
    # Position: bottom-right area
    px = W - pw - 50
    py = H - ph - 60
    
    # Paste portrait
    img.paste(portrait, (px, py), portrait)
    
    # Pink neon border around portrait
    img = neon_border(img, px - 4, py - 4, pw + 8, ph + 8, color=(255, 105, 180), glow_radius=12, thickness=3)
else:
    print(f"WARNING: No portrait found at {portrait_path}")

# ============================================================
# BYPASS LABELS
# ============================================================
bypass_data = [("SWELL", 130, 565), ("VINYL", 130, 565), ("PSYCHE", 600, 565), ("LFO", 500, 565)]
for name, bx, by in bypass_data:
    bt = make_tape(60, 16, color=(215, 205, 175))
    paste_tape(img, bt, bx - 30, by, angle=random.uniform(-1.5, 1.5))
    sharpie(img, name, bx, by + 2, label_font, center=True)

# ============================================================
# SCRATCHES
# ============================================================
scratch = Image.new("RGBA", (W, H), (0,0,0,0))
sd = ImageDraw.Draw(scratch)
for _ in range(40):
    x1 = random.randint(0, W); y1 = random.randint(0, H)
    l = random.randint(30, 160); a = random.uniform(0, math.pi)
    x2 = x1 + int(l*math.cos(a)); y2 = y1 + int(l*math.sin(a))
    sd.line([(x1,y1),(x2,y2)], fill=(210,200,185,random.randint(15,40)), width=1)
img = Image.alpha_composite(img, scratch)

out = "/tmp/aether-art/dalle_face_v2.png"
img.convert("RGB").save(out, quality=95)
print(f"Saved: {out} ({W}x{H})")
