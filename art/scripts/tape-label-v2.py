#!/usr/bin/env python3
"""
V2: Correct layout from Austin's sketch + render_final.py positions.
DALL-E skin + masking tape labels + Sharpie text.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import math
import os

random.seed(42)  # reproducible torn edges

# Load the DALL-E skin
skin = Image.open("/tmp/aether-art/dalle-skins/001-hyper-realistic-photograph-of-a-vintage-.png")

PLUGIN_W, PLUGIN_H = 960, 500

# Crop/resize skin to plugin dimensions
skin_ratio = skin.width / skin.height
plugin_ratio = PLUGIN_W / PLUGIN_H
if skin_ratio > plugin_ratio:
    new_h = skin.height
    new_w = int(new_h * plugin_ratio)
    left = (skin.width - new_w) // 2
    skin = skin.crop((left, 0, left + new_w, new_h))
else:
    new_w = skin.width
    new_h = int(new_w / plugin_ratio)
    top = (skin.height - new_h) // 2
    skin = skin.crop((0, top, new_w, top + new_h))
skin = skin.resize((PLUGIN_W, PLUGIN_H), Image.LANCZOS)

img = skin.copy().convert("RGBA")
draw = ImageDraw.Draw(img)

# --- Fonts ---
font_paths = [
    "/System/Library/Fonts/Supplemental/MarkerFelt.ttc",
    "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
]
font_file = None
for fp in font_paths:
    if os.path.exists(fp):
        font_file = fp
        break
if not font_file:
    font_file = "/System/Library/Fonts/Helvetica.ttc"

title_font = ImageFont.truetype(font_file, 26)
section_font = ImageFont.truetype(font_file, 17)
label_font = ImageFont.truetype(font_file, 11)

# --- Helpers ---
def make_tape(w, h, color=(222, 210, 180), alpha=210):
    """Fast tape strip with torn edges."""
    tape = Image.new("RGBA", (w + 6, h + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(tape)
    d.rectangle([3, 3, w + 2, h + 2], fill=(*color, alpha))
    # Slight color bands
    for _ in range(4):
        y = random.randint(3, h + 1)
        v = random.randint(-12, 12)
        c = tuple(max(0, min(255, c + v)) for c in color)
        d.rectangle([3, y, w + 2, y + random.randint(1, 2)], fill=(*c, alpha - 15))
    # Torn edges
    for x in range(w + 6):
        for dy in range(3):
            if random.random() < 0.4:
                tape.putpixel((x, dy), (0, 0, 0, 0))
            if random.random() < 0.4:
                tape.putpixel((x, h + 5 - dy), (0, 0, 0, 0))
    for y in range(h + 6):
        for dx in range(2):
            if random.random() < 0.5:
                tape.putpixel((dx, y), (0, 0, 0, 0))
            if random.random() < 0.5:
                tape.putpixel((w + 5 - dx, y), (0, 0, 0, 0))
    # Subtle shadow
    d.line([(3, h + 3), (w + 3, h + 3)], fill=(30, 25, 20, 35), width=1)
    d.line([(w + 3, 3), (w + 3, h + 3)], fill=(30, 25, 20, 35), width=1)
    return tape

def make_gaffer(w, h):
    """Dark gaffer tape."""
    return make_tape(w, h, color=(55, 52, 48), alpha=230)

def paste_tape(img, tape, x, y, angle=0):
    if angle != 0:
        tape = tape.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(tape, (x, y), tape)

def sharpie(img, text, x, y, font, color=(30, 28, 25), center=False):
    d = ImageDraw.Draw(img)
    if center:
        bbox = d.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = x - tw // 2
    # Bleed
    for dx, dy in [(-1, 0), (1, 0), (0, -1)]:
        d.text((x + dx, y + dy), text, fill=(*color, 35), font=font)
    d.text((x, y), text, fill=(*color, 255), font=font)

# --- UV to pixel (from render_final.py coordinates) ---
def uv(u_raw, v_raw):
    return int((u_raw / 1020) * PLUGIN_W), int((v_raw / 620) * PLUGIN_H)

# ============================================================
# KNOB POSITIONS (exact from render_final.py)
# ============================================================
knobs = {
    # LEFT COLUMN
    'Sens':    uv(80, 240),   'Attack':  uv(160, 240),  'Depth_S': uv(240, 240),  # Swell
    'Year':    uv(80, 355),   'Detune':  uv(160, 355),                              # Vinyl
    'Mix_M':   uv(80, 465),   'Gain':    uv(160, 465),                              # Master
    # RIGHT COLUMN
    'Shimmer': uv(455, 240),  'Space':   uv(535, 240),  'Mod':     uv(615, 240),  'Warp': uv(695, 240),  # Psyche row 1
    'Mix_P':   uv(455, 295),  'Notch':   uv(535, 295),  'Sweep':   uv(615, 295),                          # Psyche row 2
    'Shape':   uv(455, 410),  'Rate':    uv(535, 410),  'Depth_L': uv(615, 410),                          # LFO row 1
    'Div':     uv(455, 485),  'Phase':   uv(535, 485),                                                     # LFO row 2
}

# Label names for display (clean names)
knob_labels = {
    'Sens': 'Sens', 'Attack': 'Attack', 'Depth_S': 'Depth',
    'Year': 'Year', 'Detune': 'Detune',
    'Mix_M': 'Mix', 'Gain': 'Gain',
    'Shimmer': 'Shimmer', 'Space': 'Space', 'Mod': 'Mod', 'Warp': 'Warp',
    'Mix_P': 'Mix', 'Notch': 'Notch', 'Sweep': 'Sweep',
    'Shape': 'Shape', 'Rate': 'Rate', 'Depth_L': 'Depth',
    'Div': 'Div', 'Phase': 'Phase',
}

KNOB_R = 18  # knob radius in pixels

# ============================================================
# SECTION HEADERS
# ============================================================
# Swell header: above the Swell knobs
swell_hx, swell_hy = uv(80, 190)
# Vinyl header
vinyl_hx, vinyl_hy = uv(80, 305)
# Master header
master_hx, master_hy = uv(80, 425)
# Psyche header
psyche_hx, psyche_hy = uv(455, 190)
# LFO header
lfo_hx, lfo_hy = uv(455, 365)

sections = [
    ("SWELL",  swell_hx - 5,  swell_hy,  170),
    ("VINYL",  vinyl_hx - 5,  vinyl_hy,   130),
    ("MASTER", master_hx - 5, master_hy,  130),
    ("PSYCHE", psyche_hx - 5, psyche_hy,  250),
    ("LFO",    lfo_hx - 5,    lfo_hy,     200),
]

# ============================================================
# TITLE - "Austin's Secret Sauce" on gaffer tape
# ============================================================
title_text = "Austin's Secret Sauce"
gaffer_w = 350
gaffer_h = 34
gaffer = make_gaffer(gaffer_w, gaffer_h)
title_x = (PLUGIN_W - gaffer_w) // 2
title_y = 8
paste_tape(img, gaffer, title_x, title_y, angle=random.uniform(-0.5, 0.5))
# White text on dark gaffer
bbox = draw.textbbox((0, 0), title_text, font=title_font)
tw = bbox[2] - bbox[0]
sharpie(img, title_text, title_x + gaffer_w // 2, title_y + 5, title_font, color=(235, 230, 220), center=True)

# ============================================================
# SECTION LABELS on masking tape
# ============================================================
for name, sx, sy, sw in sections:
    tape = make_tape(sw, 22)
    paste_tape(img, tape, sx, sy, angle=random.uniform(-1.5, 1.5))
    sharpie(img, name, sx + sw // 2, sy + 3, section_font, center=True)

# ============================================================
# KNOB LABELS on small tape bits
# ============================================================
for key, (kx, ky) in knobs.items():
    label = knob_labels[key]
    lw = max(40, len(label) * 7 + 14)
    lh = 15
    tape = make_tape(lw, lh, color=(228, 218, 190))
    # Place label BELOW the knob
    label_y = ky + KNOB_R + 4
    label_x = kx - lw // 2
    paste_tape(img, tape, label_x, label_y, angle=random.uniform(-2, 2))
    sharpie(img, label, kx, label_y + 2, label_font, center=True)
    
    # Draw knob placeholder (white circle with indicator line)
    draw.ellipse([kx - KNOB_R, ky - KNOB_R, kx + KNOB_R, ky + KNOB_R], 
                 fill=(240, 238, 232, 200), outline=(200, 195, 185, 180), width=2)
    # Indicator slot
    draw.line([(kx, ky - KNOB_R + 3), (kx, ky - 4)], fill=(60, 55, 50, 200), width=2)

# ============================================================
# PORTRAIT placeholder (bottom right)
# ============================================================
portrait_x, portrait_y = uv(800, 380)
portrait_w, portrait_h = 130, 130
# Tape "frame" for portrait
for side_tape in [
    (portrait_x - 10, portrait_y - 10, portrait_w + 20, 18),  # top
    (portrait_x - 10, portrait_y + portrait_h - 8, portrait_w + 20, 18),  # bottom
]:
    t = make_tape(side_tape[2], side_tape[3], color=(215, 205, 175))
    paste_tape(img, t, side_tape[0], side_tape[1], angle=random.uniform(-1, 1))

# Portrait area (dark rectangle placeholder)
draw.rectangle([portrait_x, portrait_y, portrait_x + portrait_w, portrait_y + portrait_h],
               fill=(40, 35, 30, 200), outline=(60, 55, 50, 200), width=2)
sharpie(img, "PORTRAIT", portrait_x + portrait_w // 2, portrait_y + portrait_h // 2 - 8, 
        label_font, color=(150, 145, 135), center=True)

# ============================================================
# SYNC button placeholder (near LFO)
# ============================================================
sync_x, sync_y = uv(710, 450)
sync_tape = make_tape(50, 20, color=(215, 205, 175))
paste_tape(img, sync_tape, sync_x - 25, sync_y - 10, angle=random.uniform(-1, 1))
sharpie(img, "SYNC", sync_x, sync_y - 7, label_font, center=True)

# ============================================================
# SCRATCHES overlay
# ============================================================
scratch = Image.new("RGBA", (PLUGIN_W, PLUGIN_H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scratch)
for _ in range(35):
    x1 = random.randint(0, PLUGIN_W)
    y1 = random.randint(0, PLUGIN_H)
    length = random.randint(30, 150)
    angle = random.uniform(0, math.pi)
    x2 = x1 + int(length * math.cos(angle))
    y2 = y1 + int(length * math.sin(angle))
    sd.line([(x1, y1), (x2, y2)], fill=(210, 200, 185, random.randint(15, 40)), width=1)
img = Image.alpha_composite(img, scratch)

# Save
out = "/tmp/aether-art/dalle-skin-layout-v2.png"
img.convert("RGB").save(out, quality=95)
print(f"Saved: {out} ({img.size})")
