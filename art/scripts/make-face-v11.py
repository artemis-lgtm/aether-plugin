"""
Face art v11: Start from v9 (the approved design), ONLY change:
1. Replace title area with chrome nameplate
2. Replace portrait neon border with chrome frame
3. Add SYNC tape label
Everything else stays exactly as it was.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1020, 620

# Start from the APPROVED face art (v9 = thinner labels version of approved design)
skin = Image.open('/tmp/aether-art/dalle_face_v9.png').convert("RGBA")

# ---- Replace title with chrome plate ----
chrome_title = Image.open('/tmp/aether-art/chrome_title_raw.png').convert("RGBA")
chrome_title = chrome_title.resize((561, 83), Image.LANCZOS)

# Title position from the original face art
title_x, title_y = 229, 5
skin.paste(chrome_title, (title_x, title_y), chrome_title)

# ---- Replace portrait neon border with chrome frame ----
chrome_frame = Image.open('/tmp/aether-art/chrome_frame_raw.png').convert("RGBA")
chrome_frame = chrome_frame.resize((175, 175), Image.LANCZOS)

# Load portrait
portrait = Image.open('/tmp/aether-art/austin-portrait-square.jpg').convert("RGBA")
portrait = portrait.resize((155, 155), Image.LANCZOS)

# Composite portrait into chrome frame
frame_with_portrait = chrome_frame.copy()
frame_with_portrait.paste(portrait, (10, 10), portrait)

# Portrait position (same as before)
port_x, port_y = W - 175 - 35, H - 175 - 40  # = 810, 405
skin.paste(frame_with_portrait, (port_x, port_y), frame_with_portrait)

# ---- Add SYNC tape label next to sync button ----
ff = "/System/Library/Fonts/MarkerFelt.ttc"
d = ImageDraw.Draw(skin)
sync_font = ImageFont.truetype(ff, 10)

# Small tape strip background for SYNC
tape = Image.open('/tmp/aether-art/dalle-tape/001-hyper-realistic-close-up-photograph-of-a.png').convert("RGBA")
sync_tape = tape.crop((200, 200, 330, 240)).resize((48, 14), Image.LANCZOS)
sync_tape.putalpha(Image.eval(sync_tape.getchannel('A'), lambda a: min(a, 200)))
skin.paste(sync_tape, (643, 470), sync_tape)
d = ImageDraw.Draw(skin)
d.text((667, 477), "SYNC", fill=(15, 15, 15, 200), font=sync_font, anchor="mm")

skin.save('/tmp/aether-art/dalle_face_v11.png')
print(f"Saved: /tmp/aether-art/dalle_face_v11.png ({W}x{H})")
