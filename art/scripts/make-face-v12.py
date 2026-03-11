"""
Face art v12: Start from v9 (approved design), swap in DALL-E chrome plates.
Only changes: title plate, portrait frame, SYNC label. Everything else untouched.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H = 1020, 620

# Start from the APPROVED face art
skin = Image.open('/tmp/aether-art/dalle_face_v9.png').convert("RGBA")

# ---- DALL-E Chrome title plate ----
chrome_title = Image.open('/tmp/aether-art/dalle-chrome-title.png').convert("RGBA")

# The DALL-E image is 1536x1024 with the plate on black background
# Need to extract just the chrome plate and remove the black background
ct_arr = np.array(chrome_title)

# Find the chrome plate bounds (non-black region)
# Threshold: pixels brighter than 30 in any channel
bright = np.max(ct_arr[:, :, :3], axis=2) > 35
rows = np.any(bright, axis=1)
cols = np.any(bright, axis=0)
rmin, rmax = np.where(rows)[0][[0, -1]]
cmin, cmax = np.where(cols)[0][[0, -1]]

# Crop to the plate
plate = chrome_title.crop((int(cmin), int(rmin), int(cmax) + 1, int(rmax) + 1))
print(f"Chrome title plate cropped: {plate.size}")

# Make black background transparent
plate_arr = np.array(plate).astype(np.float32)
brightness = np.max(plate_arr[:, :, :3], axis=2)
# Smooth alpha: fully transparent below 30, fully opaque above 60
alpha = np.clip((brightness - 25) / 35.0, 0, 1) * 255
plate_arr[:, :, 3] = alpha
plate = Image.fromarray(plate_arr.astype(np.uint8))

# Resize to fit title area (561 x 83)
plate = plate.resize((561, 83), Image.LANCZOS)

# Place at title position
skin.paste(plate, (229, 5), plate)

# ---- DALL-E Chrome portrait frame ----
chrome_frame = Image.open('/tmp/aether-art/dalle-chrome-frame.png').convert("RGBA")

# Extract frame from black background
cf_arr = np.array(chrome_frame)
bright_f = np.max(cf_arr[:, :, :3], axis=2) > 35
rows_f = np.any(bright_f, axis=1)
cols_f = np.any(bright_f, axis=0)
rmin_f, rmax_f = np.where(rows_f)[0][[0, -1]]
cmin_f, cmax_f = np.where(cols_f)[0][[0, -1]]

frame = chrome_frame.crop((int(cmin_f), int(rmin_f), int(cmax_f) + 1, int(rmax_f) + 1))
print(f"Chrome frame cropped: {frame.size}")

# Make black transparent
frame_arr = np.array(frame).astype(np.float32)
brightness_f = np.max(frame_arr[:, :, :3], axis=2)
alpha_f = np.clip((brightness_f - 25) / 35.0, 0, 1) * 255
frame_arr[:, :, 3] = alpha_f
frame = Image.fromarray(frame_arr.astype(np.uint8))

# Resize to 175x175
frame = frame.resize((175, 175), Image.LANCZOS)

# Composite portrait into the frame's center opening
portrait = Image.open('/tmp/aether-art/austin-portrait-square.jpg').convert("RGBA")
portrait = portrait.resize((125, 125), Image.LANCZOS)

# Find the dark center of the frame to place portrait
# The frame should have a dark opening in the middle
frame_center = frame.copy()
# Place portrait at center
px_off = (175 - 125) // 2
frame_center.paste(portrait, (px_off, px_off))
# Then paste the chrome frame border on top (so frame overlaps portrait edges)
frame_center.paste(frame, (0, 0), frame)

# Place at portrait position
port_x, port_y = W - 175 - 35, H - 175 - 40  # 810, 405
skin.paste(frame_center, (port_x, port_y), frame_center)

# ---- SYNC tape label ----
ff = "/System/Library/Fonts/MarkerFelt.ttc"
tape = Image.open('/tmp/aether-art/dalle-tape/001-hyper-realistic-close-up-photograph-of-a.png').convert("RGBA")
sync_tape = tape.crop((200, 200, 330, 240)).resize((48, 14), Image.LANCZOS)
sync_tape.putalpha(Image.eval(sync_tape.getchannel('A'), lambda a: min(a, 200)))
skin.paste(sync_tape, (643, 470), sync_tape)
d = ImageDraw.Draw(skin)
sync_font = ImageFont.truetype(ff, 10)
d.text((667, 477), "SYNC", fill=(15, 15, 15, 200), font=sync_font, anchor="mm")

skin.save('/tmp/aether-art/dalle_face_v12.png')
print(f"Saved: /tmp/aether-art/dalle_face_v12.png ({W}x{H})")
