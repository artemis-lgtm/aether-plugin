"""Generate a preview composite of the plugin UI."""
from PIL import Image, ImageDraw
import os

# Load face art background
bg = Image.open('/tmp/aether-plugin/resources/background.png').convert('RGBA')
W, H = bg.size  # 1020x620

# Knob positions from PluginEditor.cpp (center x, center y)
K = 50  # knob display size
KNOB_POSITIONS = {
    'swellsens':     (80, 240),
    'swellattack':   (160, 240),
    'swelldepth':    (240, 240),
    'vinylyear':     (80, 355),
    'vinyldetune':   (160, 355),
    'psycheshimmer': (420, 240),
    'psychespace':   (490, 240),
    'psychemod':     (560, 240),
    'psychewarp':    (630, 240),
    'psychemix':     (700, 240),
    'psychenotches': (770, 240),
    'psychesweep':   (840, 240),
    'lfoshape':      (455, 410),
    'lforate':       (525, 410),
    'lfodepth':      (595, 410),
    'lfosyncrate':   (455, 485),
    'lfophase':      (525, 485),
    'mastermix':     (80, 465),
    'mastergain':    (160, 465),
}

# Draw each knob (frame 64 = noon position)
for name, (cx, cy) in KNOB_POSITIONS.items():
    strip_path = f'/tmp/aether-plugin/resources/knob-{name}.png'
    if not os.path.exists(strip_path):
        continue
    strip = Image.open(strip_path).convert('RGBA')
    # Extract frame 64 (middle position)
    frame_size = strip.height  # 128
    frame = strip.crop((64 * frame_size, 0, 65 * frame_size, frame_size))
    frame = frame.resize((K, K), Image.LANCZOS)
    # Paste centered
    bg.paste(frame, (cx - K//2, cy - K//2), frame)

# Draw LED indicators (simple colored dots)
draw = ImageDraw.Draw(bg)
led_size = 12
leds = [
    (290, 195, (0, 255, 80)),   # swell bypass
    (220, 310, (0, 255, 80)),   # vinyl bypass  
    (700, 348, (0, 255, 80)),   # lfo bypass
    (680, 470, (255, 200, 50)), # sync
    (730, 470, (100, 150, 255)), # upbeat
]
# psyche bypass - need to calc
psycheStart = 420
psycheGap = 70
px = psycheStart + psycheGap*6 + K//2 + 40
leds.append((px, 195, (0, 255, 80)))

for lx, ly, color in leds:
    draw.ellipse([lx-led_size//2, ly-led_size//2, lx+led_size//2, ly+led_size//2], 
                 fill=color, outline=(40,40,40))

# Save
out = '/tmp/aether-art/preview_v4.11.png'
bg.save(out)
print(f"Saved: {out} ({bg.size[0]}x{bg.size[1]})")
