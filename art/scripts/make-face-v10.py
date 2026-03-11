"""
Face art v10:
- Chrome title plate (Blender rendered) replaces black+neon title
- Chrome portrait frame replaces neon border
- Bigger/thicker label text (still legible)
- SYNC tape label next to sync button
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1020, 620

# Load base skin (DALL-E art stretched to fill)
skin = Image.open('/tmp/aether-art/dalle-skins/001-hyper-realistic-photograph-of-a-vintage-.png').convert("RGBA")
skin = skin.resize((W, H), Image.LANCZOS)

d = ImageDraw.Draw(skin)

# ---- Duct tape strips for section headers ----
tape = Image.open('/tmp/aether-art/dalle-tape/001-hyper-realistic-close-up-photograph-of-a.png').convert("RGBA")

# Section tape headers with positions
sections = [
    ("SWELL",  (30, 190, 280, 220)),
    ("VINYL",  (30, 305, 200, 335)),
    ("MASTER", (30, 420, 200, 450)),
    ("PSYCHE", (380, 190, 870, 220)),
    ("LFO",    (380, 360, 660, 390)),
]

for label, (x1, y1, x2, y2) in sections:
    tw = x2 - x1
    th = y2 - y1
    tape_strip = tape.crop((100, 100, 100 + tw * 2, 100 + th * 2)).resize((tw, th), Image.LANCZOS)
    # Make tape slightly transparent
    tape_strip.putalpha(Image.eval(tape_strip.getchannel('A'), lambda a: min(a, 210)))
    skin.paste(tape_strip, (x1, y1), tape_strip)

    # Section name on tape - Sharpie style
    ff = "/System/Library/Fonts/MarkerFelt.ttc"
    header_font = ImageFont.truetype(ff, 22)
    d = ImageDraw.Draw(skin)
    # Slight shadow
    d.text((x1 + tw//2 + 1, y1 + th//2 + 1), label, fill=(0, 0, 0, 60), font=header_font, anchor="mm")
    d.text((x1 + tw//2, y1 + th//2), label, fill=(20, 20, 20, 230), font=header_font, anchor="mm")

# ---- Knob labels (bigger, thicker, legible) ----
ff = "/System/Library/Fonts/MarkerFelt.ttc"
label_font = ImageFont.truetype(ff, 13)  # bigger than 10, smaller than 14

KNOB_R_UV = 24  # label offset below knob center

knob_labels = [
    # Swell (left column)
    ("SENS",    80,  240 + KNOB_R_UV),
    ("ATTACK", 160,  240 + KNOB_R_UV),
    ("DEPTH",  240,  240 + KNOB_R_UV),
    # Vinyl
    ("YEAR",    80,  355 + KNOB_R_UV),
    ("DETUNE", 160,  355 + KNOB_R_UV),
    # Master
    ("MIX",     80,  465 + KNOB_R_UV),
    ("GAIN",   160,  465 + KNOB_R_UV),
    # Psyche (7 knobs, gap=70, start=420)
    ("SHIMMER", 420, 240 + KNOB_R_UV),
    ("SPACE",   490, 240 + KNOB_R_UV),
    ("MOD",     560, 240 + KNOB_R_UV),
    ("WARP",    630, 240 + KNOB_R_UV),
    ("MIX",     700, 240 + KNOB_R_UV),
    ("NOTCH",   770, 240 + KNOB_R_UV),
    ("SWEEP",   840, 240 + KNOB_R_UV),
    # LFO
    ("SHAPE",   455, 410 + KNOB_R_UV),
    ("RATE",    535, 410 + KNOB_R_UV),
    ("DEPTH",   615, 410 + KNOB_R_UV),
    ("SYNC RT", 455, 485 + KNOB_R_UV),
    ("PHASE",   535, 485 + KNOB_R_UV),
]

d = ImageDraw.Draw(skin)
for text, x, y in knob_labels:
    # Sharpie: medium weight, slight bleed for hand-drawn feel
    color = (15, 15, 15)
    for dx, dy in [(-1, 0), (1, 0), (0, -1)]:
        d.text((x + dx, y + dy), text, fill=(*color, 35), font=label_font, anchor="mt")
    d.text((x, y), text, fill=(*color, 200), font=label_font, anchor="mt")

# ---- SYNC tape label ----
sync_tape = tape.crop((200, 200, 330, 240)).resize((50, 16), Image.LANCZOS)
sync_tape.putalpha(Image.eval(sync_tape.getchannel('A'), lambda a: min(a, 200)))
skin.paste(sync_tape, (640, 468), sync_tape)
d = ImageDraw.Draw(skin)
sync_font = ImageFont.truetype(ff, 10)
d.text((665, 476), "SYNC", fill=(15, 15, 15, 200), font=sync_font, anchor="mm")

# ---- Chrome title plate ----
chrome_title = Image.open('/tmp/aether-art/chrome_title_raw.png').convert("RGBA")
chrome_title = chrome_title.resize((561, 83), Image.LANCZOS)

# Place at title position (229, 5)
# First clear that area on skin
title_x, title_y = 229, 5
skin.paste(chrome_title, (title_x, title_y), chrome_title)

# ---- Chrome portrait frame ----
chrome_frame = Image.open('/tmp/aether-art/chrome_frame_raw.png').convert("RGBA")
chrome_frame = chrome_frame.resize((175, 175), Image.LANCZOS)

# Load portrait
portrait = Image.open('/tmp/aether-art/austin-portrait-square.jpg').convert("RGBA")
portrait = portrait.resize((155, 155), Image.LANCZOS)

# Composite portrait into chrome frame (center it)
frame_with_portrait = chrome_frame.copy()
portrait_offset = (10, 10)  # border is ~10px
frame_with_portrait.paste(portrait, portrait_offset, portrait)

# Place at portrait position (810, 405)
port_x, port_y = 810, 405
skin.paste(frame_with_portrait, (port_x, port_y), frame_with_portrait)

# ---- Footswitch indicator ----
foot_x = int(0.35 * W)
foot_y = int(0.88 * H)
d = ImageDraw.Draw(skin)
d.ellipse([foot_x - 20, foot_y - 20, foot_x + 20, foot_y + 20], fill=(80, 80, 85, 180))
d.ellipse([foot_x - 15, foot_y - 15, foot_x + 15, foot_y + 15], fill=(50, 50, 55, 200))

skin.save('/tmp/aether-art/dalle_face_v10.png')
print(f"Saved: /tmp/aether-art/dalle_face_v10.png ({W}x{H})")
