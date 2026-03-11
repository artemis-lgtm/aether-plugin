#!/usr/bin/env python3
"""
V6 face: Bigger title, sharper/bolder knob labels.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random, math, os

random.seed(42)

skin = Image.open("/tmp/aether-art/dalle-wood/001-hyper-realistic-top-down-photograph-of-a.png")
W, H = 1020, 620
skin = skin.resize((W, H), Image.LANCZOS)
img = skin.copy().convert("RGBA")

# Edge extend
for x in range(W):
    c = img.getpixel((x, 3)); [img.putpixel((x, y), c) for y in range(3)]
    c = img.getpixel((x, H-4)); [img.putpixel((x, y), c) for y in range(H-3, H)]
for y in range(H):
    c = img.getpixel((5, y)); [img.putpixel((x, y), c) for x in range(5)]
    c = img.getpixel((W-6, y)); [img.putpixel((x, y), c) for x in range(W-5, W)]

# Load DALL-E duct tape
tape_src = Image.open("/tmp/aether-art/dalle-tape/001-hyper-realistic-close-up-photograph-of-a.png").convert("RGBA")
tw, th = tape_src.size
tape_region = tape_src.crop((int(tw*0.05), int(th*0.25), int(tw*0.95), int(th*0.75)))

def make_duct_tape_strip(width, height, tape_region=tape_region):
    strip = tape_region.resize((width + 20, height + 10), Image.LANCZOS)
    sw, sh = strip.size
    left = (sw - width) // 2; top = (sh - height) // 2
    strip = strip.crop((left, top, left + width, top + height))
    mask = Image.new("L", (width, height), 255)
    md = ImageDraw.Draw(mask)
    for y in range(height):
        tear = random.randint(0, 4)
        for x in range(tear): mask.putpixel((x, y), 0)
        tear = random.randint(0, 4)
        for x in range(width - tear, width): mask.putpixel((x, y), 0)
    for x in range(width):
        if random.random() < 0.3: mask.putpixel((x, 0), 0)
        if random.random() < 0.3: mask.putpixel((x, height - 1), 0)
    strip.putalpha(mask)
    shadow = Image.new("RGBA", (width + 4, height + 4), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([2, 2, width + 1, height + 1], fill=(0, 0, 0, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))
    result = Image.new("RGBA", (width + 4, height + 4), (0, 0, 0, 0))
    result = Image.alpha_composite(result, shadow)
    result.paste(strip, (1, 1), strip)
    return result

def paste_strip(img, strip, x, y, angle=0):
    if angle: strip = strip.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(strip, (x, y), strip)

# ============================================================
# FONTS -- sharper, bolder
# ============================================================
ff = None
for fp in ["/System/Library/Fonts/Supplemental/MarkerFelt.ttc",
           "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf"]:
    if os.path.exists(fp): ff = fp; break
if not ff: ff = "/System/Library/Fonts/Helvetica.ttc"

# Try to get a bold variant for sharper text
try:
    ff_bold = ff  # same font, not bold
    if not os.path.exists(ff_bold):
        ff_bold = ff  # same font, not bold
    if not os.path.exists(ff_bold):
        ff_bold = ff  # same font, not bold
except:
    ff_bold = ff  # same font, not bold

title_font = ImageFont.truetype(ff, 58)  # EVEN BIGGER
sect_font = ImageFont.truetype(ff, 20)
label_font = ImageFont.truetype(ff, 10)  # very thin, light

NEON_RED = (255, 40, 40)

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
    for dx2 in range(-5, 6):
        for dy2 in range(-5, 6):
            dist = math.sqrt(dx2*dx2 + dy2*dy2)
            if dist <= 5:
                alpha = int(75 * (1 - dist / 5))
                gd.text((x+dx2, y+dy2), text, fill=(*color, alpha), font=font)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=5))
    gd2 = ImageDraw.Draw(glow)
    inner = (255, min(255,color[1]+120), min(255,color[2]+120))
    gd2.text((x, y), text, fill=(*inner, 255), font=font)
    return Image.alpha_composite(img, glow)

def sharpie_bold(img, text, x, y, font, color=(10, 8, 5), center=False, thin=False):
    """Sharpie text. thin=True for lighter single stroke."""
    d = ImageDraw.Draw(img)
    if center:
        bb = d.textbbox((0,0), text, font=font)
        x = x - (bb[2] - bb[0]) // 2
    if thin:
        # Ultra light single stroke
        d.text((x, y), text, fill=(*color, 180), font=font)
    else:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                d.text((x+dx, y+dy), text, fill=(*color, 180), font=font)
        d.text((x, y), text, fill=(*color, 255), font=font)

# ============================================================
# TITLE -- EVEN BIGGER
# ============================================================
title_text = "Austin's Secret Sauce"
draw = ImageDraw.Draw(img)
bb = draw.textbbox((0,0), title_text, font=title_font)
tw_t = bb[2] - bb[0]; th_t = bb[3] - bb[1]
pad_x, pad_y = 35, 16
box_w = tw_t + pad_x * 2; box_h = th_t + pad_y * 2
bx = (W - box_w) // 2; by = 5

backing = Image.new("RGBA", (box_w, box_h), (25, 20, 15, 210))
img.paste(backing, (bx, by), backing)
img = neon_border(img, bx, by, box_w, box_h, color=NEON_RED, glow_radius=16, thickness=5)
img = neon_text(img, title_text, bx + box_w // 2, by + pad_y - 4, title_font, color=NEON_RED, center=True)

# ============================================================
# SECTION HEADERS
# ============================================================
sections = [
    ("SWELL",   40,  185,  220, 28),
    ("VINYL",   40,  300,  160, 28),
    ("MASTER",  40,  415,  160, 28),
    ("PSYCHE",  385, 185,  490, 28),
    ("LFO",     415, 358,  240, 28),
]
for name, sx, sy, sw, sh in sections:
    strip = make_duct_tape_strip(sw, sh)
    paste_strip(img, strip, sx, sy, angle=random.uniform(-1.2, 1.2))
    sharpie_bold(img, name, sx + sw // 2, sy + 5, sect_font, center=True)

# ============================================================
# KNOB LABELS -- sharper, bolder, slightly bigger tape
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
KNOB_R_UV = 24  # tighter to knobs

for name, kx, ky in knob_data:
    lw = max(55, len(name) * 10 + 16)
    lh = 22
    strip = make_duct_tape_strip(lw, lh)
    ly = ky + KNOB_R_UV + 6
    lx = kx - lw // 2
    paste_strip(img, strip, lx, ly, angle=random.uniform(-1.8, 1.8))
    sharpie_bold(img, name, kx, ly + 4, label_font, center=True, thin=True)

# SYNC
strip = make_duct_tape_strip(60, 22)
paste_strip(img, strip, 697, 443, angle=random.uniform(-1, 1))
sharpie_bold(img, "SYNC", 727, 447, label_font, center=True, thin=True)

# ============================================================
# PORTRAIT
# ============================================================
portrait_path = "/tmp/aether-art/austin-portrait-square.jpg"
if os.path.exists(portrait_path):
    portrait = Image.open(portrait_path).convert("RGBA")
    pw, ph = 175, 175
    portrait = portrait.resize((pw, ph), Image.LANCZOS)
    px = W - pw - 35; py = H - ph - 40
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

out = "/tmp/aether-art/dalle_face_v9.png"
img.convert("RGB").save(out, quality=95)
print(f"Saved: {out} ({W}x{H})")
