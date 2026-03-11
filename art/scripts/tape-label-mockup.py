#!/usr/bin/env python3
"""
Overlay masking tape labels on the DALL-E skin.
Tape strips with hand-written Sharpie text for all labels.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import math
import os

# Load the DALL-E skin
skin = Image.open("/tmp/aether-art/dalle-skins/001-hyper-realistic-photograph-of-a-vintage-.png")

# Plugin dimensions from the existing layout
PLUGIN_W, PLUGIN_H = 960, 500

# Resize/crop the skin to fit plugin dimensions
skin_ratio = skin.width / skin.height
plugin_ratio = PLUGIN_W / PLUGIN_H

if skin_ratio > plugin_ratio:
    # Skin is wider - crop sides
    new_h = skin.height
    new_w = int(new_h * plugin_ratio)
    left = (skin.width - new_w) // 2
    skin = skin.crop((left, 0, left + new_w, new_h))
else:
    # Skin is taller - crop top/bottom
    new_w = skin.width
    new_h = int(new_w / plugin_ratio)
    top = (skin.height - new_h) // 2
    skin = skin.crop((0, top, new_w, top + new_h))

skin = skin.resize((PLUGIN_W, PLUGIN_H), Image.LANCZOS)

# Create working image
img = skin.copy().convert("RGBA")

def make_tape_strip(width, height, color=(222, 210, 180), torn_edges=True):
    """Create a masking tape strip with realistic texture."""
    tape = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tape)
    
    # Base tape color with slight variation
    for y in range(height):
        for x in range(width):
            # Semi-transparent tape
            r = color[0] + random.randint(-8, 8)
            g = color[1] + random.randint(-8, 8)
            b = color[2] + random.randint(-8, 8)
            a = random.randint(200, 230)
            
            # Torn edges - fade alpha near edges
            if torn_edges:
                edge_dist = min(x, width - x, y, height - y)
                if edge_dist < 3:
                    a = int(a * (edge_dist / 3.0) + random.randint(-20, 20))
                    a = max(0, min(255, a))
            
            tape.putpixel((x, y), (min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b)), a))
    
    # Add some wrinkle lines
    draw = ImageDraw.Draw(tape)
    for _ in range(3):
        y_pos = random.randint(2, height - 3)
        draw.line([(0, y_pos), (width, y_pos + random.randint(-1, 1))], 
                  fill=(color[0]-20, color[1]-20, color[2]-20, 60), width=1)
    
    return tape

def make_tape_strip_fast(width, height, color=(222, 210, 180)):
    """Faster tape strip using drawing primitives."""
    tape = Image.new("RGBA", (width + 4, height + 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tape)
    
    # Main tape body
    base_alpha = 215
    draw.rectangle([2, 2, width + 1, height + 1], fill=(*color, base_alpha))
    
    # Slight color variation strips (horizontal)
    for i in range(5):
        y = random.randint(2, height)
        variation = random.randint(-15, 15)
        c = tuple(max(0, min(255, c + variation)) for c in color)
        draw.rectangle([2, y, width + 1, y + random.randint(1, 3)], fill=(*c, base_alpha - 10))
    
    # Torn edge effect - irregular edges
    for x in range(width + 4):
        # Top edge
        if random.random() < 0.3:
            tape.putpixel((x, 0), (0, 0, 0, 0))
            tape.putpixel((x, 1), (0, 0, 0, 0))
        # Bottom edge
        if random.random() < 0.3:
            tape.putpixel((x, height + 3), (0, 0, 0, 0))
            tape.putpixel((x, height + 2), (0, 0, 0, 0))
    
    # Wrinkle lines
    for _ in range(2):
        y_pos = random.randint(4, height - 2)
        draw.line([(3, y_pos), (width, y_pos + random.randint(-1, 1))], 
                  fill=(color[0]-25, color[1]-25, color[2]-25, 50), width=1)
    
    # Shadow on bottom-right
    for x in range(3, width + 2):
        tape.putpixel((x, height + 2), (40, 30, 20, 40))
    for y in range(3, height + 2):
        tape.putpixel((width + 2, y), (40, 30, 20, 40))
    
    return tape

def draw_sharpie_text(img, text, x, y, font, color=(30, 30, 35)):
    """Draw text that looks like Sharpie marker -- slight bleed/roughness."""
    draw = ImageDraw.Draw(img)
    # Slight shadow/bleed
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.text((x + dx, y + dy), text, fill=(*color, 40), font=font)
    # Main text
    draw.text((x, y), text, fill=(*color, 255), font=font)

# Try to find a handwriting-style font
font_paths = [
    "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
    "/System/Library/Fonts/Supplemental/Noteworthy.ttc",
    "/System/Library/Fonts/Supplemental/MarkerFelt.ttc",
    "/Library/Fonts/MarkerFelt.ttc",
]

sharpie_font_large = None
sharpie_font_med = None
sharpie_font_small = None

for fp in font_paths:
    if os.path.exists(fp):
        try:
            sharpie_font_large = ImageFont.truetype(fp, 22)
            sharpie_font_med = ImageFont.truetype(fp, 16)
            sharpie_font_small = ImageFont.truetype(fp, 12)
            print(f"Using font: {fp}")
            break
        except:
            continue

if sharpie_font_large is None:
    sharpie_font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    sharpie_font_med = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    sharpie_font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    print("Fallback to Helvetica")

# Title font (bigger)
title_font = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            title_font = ImageFont.truetype(fp, 28)
            break
        except:
            continue
if title_font is None:
    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)

# ---- LAYOUT ----
# Section positions (approximate, matching existing plugin layout)
# 5 sections across: SWELL | VINYL | PSYCHE | LFO | MASTER

sections = {
    "SWELL":  {"x": 20,  "w": 175, "knobs": ["Sensitivity", "Attack", "Depth"]},
    "VINYL":  {"x": 200, "w": 155, "knobs": ["Year", "Detune"]},
    "PSYCHE": {"x": 360, "w": 255, "knobs": ["Chorus", "Delay", "Shimmer", "Feedback", "Notch", "Depth", "Mix"]},
    "LFO":    {"x": 620, "w": 210, "knobs": ["Rate", "Depth", "Shape", "Phase", "Sync"]},
    "MASTER": {"x": 835, "w": 115, "knobs": ["Mix", "Gain"]},
}

SECTION_Y = 28  # Y position for section headers
KNOB_ROW_Y = 85  # Y position for knob row
KNOB_SPACING = 48  # Horizontal spacing between knobs
LABEL_Y_OFFSET = 55  # Label below knob center

# ---- DRAW TITLE ----
title_text = "AUSTIN'S SECRET SAUCE"
# Gaffer tape for title (darker, wider)
gaffer_w = 400
gaffer_h = 36
gaffer = make_tape_strip_fast(gaffer_w, gaffer_h, color=(50, 50, 55))
title_x = (PLUGIN_W - gaffer_w) // 2
title_y = 2
img.paste(gaffer, (title_x, title_y), gaffer)

# White paint marker on dark gaffer tape
draw = ImageDraw.Draw(img)
bbox = draw.textbbox((0, 0), title_text, font=title_font)
tw = bbox[2] - bbox[0]
text_x = title_x + (gaffer_w - tw) // 2
text_y = title_y + 4
draw_sharpie_text(img, title_text, text_x, text_y, title_font, color=(230, 225, 215))

# ---- DRAW SECTIONS ----
for sect_name, sect in sections.items():
    # Section header tape
    tape_w = sect["w"] - 10
    tape_h = 22
    tape = make_tape_strip_fast(tape_w, tape_h, color=(222, 210, 180))
    
    # Slight random rotation for realism
    angle = random.uniform(-1.5, 1.5)
    tape = tape.rotate(angle, expand=True, resample=Image.BICUBIC)
    
    tape_x = sect["x"] + 5
    tape_y = SECTION_Y
    img.paste(tape, (tape_x, tape_y), tape)
    
    # Section name in Sharpie
    bbox = draw.textbbox((0, 0), sect_name, font=sharpie_font_med)
    tw = bbox[2] - bbox[0]
    text_x = sect["x"] + (sect["w"] - tw) // 2
    draw_sharpie_text(img, sect_name, text_x, tape_y + 3, sharpie_font_med)
    
    # Knob labels
    num_knobs = len(sect["knobs"])
    knob_start_x = sect["x"] + 15
    
    # Distribute knobs evenly across section width
    if num_knobs == 1:
        positions = [sect["x"] + sect["w"] // 2]
    else:
        usable_w = sect["w"] - 30
        spacing = usable_w / (num_knobs - 1) if num_knobs > 1 else 0
        positions = [knob_start_x + int(i * spacing) for i in range(num_knobs)]
    
    for i, (knob_name, kx) in enumerate(zip(sect["knobs"], positions)):
        # Small tape piece for each label
        label_tape_w = max(45, len(knob_name) * 8 + 16)
        label_tape_h = 16
        label_tape = make_tape_strip_fast(label_tape_w, label_tape_h, color=(228, 218, 190))
        
        # Slight rotation
        angle = random.uniform(-2.5, 2.5)
        label_tape = label_tape.rotate(angle, expand=True, resample=Image.BICUBIC)
        
        label_x = kx - label_tape_w // 2
        label_y = KNOB_ROW_Y + LABEL_Y_OFFSET
        
        img.paste(label_tape, (label_x, label_y), label_tape)
        
        # Knob label text
        bbox = draw.textbbox((0, 0), knob_name, font=sharpie_font_small)
        tw = bbox[2] - bbox[0]
        draw_sharpie_text(img, knob_name, kx - tw // 2, label_y + 2, sharpie_font_small)

    # Draw knob placeholders (circles where knobs will go)
    for kx in positions:
        # Light circle to show knob position
        r = 18
        ky = KNOB_ROW_Y + 15
        draw.ellipse([kx - r, ky - r, kx + r, ky + r], outline=(255, 255, 255, 60), width=1)

# ---- BYPASS BUTTONS (bottom row) ----
bypass_labels = ["SWELL", "VINYL", "PSYCHE", "LFO"]
bypass_y = PLUGIN_H - 55
for i, label in enumerate(bypass_labels):
    sect = sections[label]
    bx = sect["x"] + sect["w"] // 2
    
    # Small tape for bypass label
    bt_w = 55
    bt_h = 14
    bt = make_tape_strip_fast(bt_w, bt_h, color=(215, 205, 175))
    bt = bt.rotate(random.uniform(-2, 2), expand=True, resample=Image.BICUBIC)
    img.paste(bt, (bx - bt_w // 2, bypass_y + 18), bt)
    
    bbox = draw.textbbox((0, 0), label, font=sharpie_font_small)
    tw = bbox[2] - bbox[0]
    draw_sharpie_text(img, label, bx - tw // 2, bypass_y + 19, sharpie_font_small)

# ---- ADD SCRATCHES ----
scratch_layer = Image.new("RGBA", (PLUGIN_W, PLUGIN_H), (0, 0, 0, 0))
scratch_draw = ImageDraw.Draw(scratch_layer)
for _ in range(30):
    x1 = random.randint(0, PLUGIN_W)
    y1 = random.randint(0, PLUGIN_H)
    length = random.randint(20, 120)
    angle = random.uniform(0, math.pi)
    x2 = x1 + int(length * math.cos(angle))
    y2 = y1 + int(length * math.sin(angle))
    alpha = random.randint(15, 45)
    scratch_draw.line([(x1, y1), (x2, y2)], fill=(200, 195, 185, alpha), width=1)

img = Image.alpha_composite(img, scratch_layer)

# Save
output_path = "/tmp/aether-art/dalle-skin-with-labels-v1.png"
img.convert("RGB").save(output_path, quality=95)
print(f"Saved: {output_path}")
print(f"Size: {img.size}")

