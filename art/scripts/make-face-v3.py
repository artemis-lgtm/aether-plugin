#!/usr/bin/env python3
"""
V3 Face skin:
- No bypass labels at bottom (removed VINYL, LFO, PSYCHE bottom labels)
- Portrait bigger with bigger border
- Skin OVER-stretched so no black strips on sides -- we'll make it wider than 1020 
  and let the UV mapping handle it, or just ensure the artwork fills every pixel
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math, os

random.seed(42)

skin = Image.open("/tmp/aether-art/dalle-skins/001-hyper-realistic-photograph-of-a-vintage-.png")
W, H = 1020, 620

# STRETCH: resize the skin to be slightly WIDER than needed, then center-crop
# This ensures no black edges remain on the pedal face
# The DALL-E image is 1536x1024 -- let's fill height and overflow width
scale_h = H / skin.height
scaled_w = int(skin.width * scale_h)
if scaled_w < W:
    # If still not wide enough, scale by width instead
    scale_w = W / skin.width
    scaled_h = int(skin.height * scale_w)
    skin = skin.resize((W, scaled_h), Image.LANCZOS)
    top = (scaled_h - H) // 2
    skin = skin.crop((0, top, W, top + H))
else:
    skin = skin.resize((scaled_w, H), Image.LANCZOS)
    left = (scaled_w - W) // 2
    skin = skin.crop((left, 0, left + W, H))

# Now extend the edges: sample the edge colors and paint a gradient outward
# to ensure absolutely no black at the UV mapping boundaries
img = skin.copy().convert("RGBA")

# Fill any remaining edge pixels by stretching the edge columns/rows
for x in range(W):
    # Top 3 rows - replicate row 3
    c = img.getpixel((x, 3))
    for y in range(3):
        img.putpixel((x, y), c)
    # Bottom 3 rows
    c = img.getpixel((x, H - 4))
    for y in range(H - 3, H):
        img.putpixel((x, y), c)

for y in range(H):
    # Left 5 cols
    c = img.getpixel((5, y))
    for x in range(5):
        img.putpixel((x, y), c)
    # Right 5 cols
    c = img.getpixel((W - 6, y))
    for x in range(W - 5, W):
        img.putpixel((x, y), c)

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

def neon_border(img, x, y, w, h, color=(255, 105, 180), glow_radius=10, thickness=3):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(glow_radius, 0, -1):
        alpha = int(80 * (1 - r / glow_radius))
        gd.rectangle([x-r, y-r, x+w+r, y+h+r], outline=(*color, alpha), width=2)
    gd.rectangle([x, y, x+w, y+h], outline=(*color, 255), width=thickness)
    inner = (min(255,color[0]+80), min(255,color[1]+80), min(255,color[2]+80))
    gd.rectangle([x+1, y+1, x+w-1, y+h-1], outline=(*inner, 140), width=1)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=4))
    gd2 = ImageDraw.Draw(glow)
    gd2.rectangle([x, y, x+w, y+h], outline=(*color, 240), width=thickness)
    gd2.rectangle([x+1, y+1, x+w-1, y+h-1], outline=(*inner, 120), width=1)
    return Image.alpha_composite(img, glow)

def neon_text(img, text, x, y, font, color=(255, 105, 180), center=False):
    d = ImageDraw.Draw(img)
    if center:
        bb = d.textbbox((0,0), text, font=font)
        x = x - (bb[2] - bb[0]) // 2
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for dx2 in range(-3, 4):
        for dy2 in range(-3, 4):
            dist = math.sqrt(dx2*dx2 + dy2*dy2)
            if dist <= 3:
                alpha = int(60 * (1 - dist / 3))
                gd.text((x+dx2, y+dy2), text, fill=(*color, alpha), font=font)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
    gd2 = ImageDraw.Draw(glow)
    inner = (min(255,color[0]+60), min(255,color[1]+60), min(255,color[2]+60))
    gd2.text((x, y), text, fill=(*inner, 255), font=font)
    return Image.alpha_composite(img, glow)

# ============================================================
# KNOB POSITIONS (Psyche: 7 in a row)
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

sections = [
    ("SWELL",   40,  185,  220),
    ("VINYL",   40,  300,  160),
    ("MASTER",  40,  415,  160),
    ("PSYCHE",  385, 185,  490),
    ("LFO",     415, 358,  240),
]

# ============================================================
# TITLE
# ============================================================
title_text = "Austin's Secret Sauce"
gw, gh = 480, 50
g = make_gaffer(gw, gh)
tx = (W - gw) // 2
ty = 15
paste_tape(img, g, tx, ty, angle=0)
img = neon_border(img, tx, ty, gw, gh, color=(255, 105, 180), glow_radius=10, thickness=3)
img = neon_text(img, title_text, tx + gw // 2, ty + 8, title_font, color=(255, 105, 180), center=True)

# ============================================================
# SECTION HEADERS
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
# NO BYPASS LABELS AT BOTTOM (removed per Austin)
# ============================================================

# ============================================================
# AUSTIN'S PORTRAIT - BIGGER with bigger pink neon frame
# ============================================================
portrait_path = "/tmp/aether-art/austin-portrait-square.jpg"
if os.path.exists(portrait_path):
    portrait = Image.open(portrait_path).convert("RGBA")
    pw, ph = 175, 175  # BIGGER
    portrait = portrait.resize((pw, ph), Image.LANCZOS)
    px = W - pw - 35
    py = H - ph - 40
    img.paste(portrait, (px, py), portrait)
    img = neon_border(img, px - 6, py - 6, pw + 12, ph + 12, 
                       color=(255, 105, 180), glow_radius=14, thickness=4)
else:
    print(f"WARNING: No portrait at {portrait_path}")

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

out = "/tmp/aether-art/dalle_face_v3.png"
img.convert("RGB").save(out, quality=95)
print(f"Saved: {out} ({W}x{H})")
