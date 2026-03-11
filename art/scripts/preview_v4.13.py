"""Generate preview composite matching exactly what the plugin looks like."""
from PIL import Image, ImageDraw
import os

bg = Image.open('/tmp/aether-plugin/resources/background.png').convert('RGBA')
W, H = bg.size

K = 50
# Exact positions from v4.8 PluginEditor.cpp resized()
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

for name, (cx, cy) in KNOB_POSITIONS.items():
    strip_path = f'/tmp/aether-plugin/resources/knob-{name}.png'
    if not os.path.exists(strip_path):
        continue
    strip = Image.open(strip_path).convert('RGBA')
    frame_size = strip.height
    frame = strip.crop((64 * frame_size, 0, 65 * frame_size, frame_size))
    frame = frame.resize((K, K), Image.LANCZOS)
    bg.paste(frame, (cx - K//2, cy - K//2), frame)

# LEDs at v4.8 positions
draw = ImageDraw.Draw(bg)
ledS = 14
leds = [
    (270, 195, (0, 255, 80)),   # swell bypass
    (190, 310, (0, 255, 80)),   # vinyl bypass
    (648, 368, (0, 255, 80)),   # lfo bypass
    (620, 470, (255, 200, 50)), # sync
    (650, 470, (100, 150, 255)), # upbeat (new)
]
# psyche bypass
psycheStart, psycheGap = 420, 70
px = psycheStart + psycheGap*6 + K//2 + 8
leds.append((px, 195, (0, 255, 80)))

for lx, ly, color in leds:
    draw.ellipse([lx-ledS//2, ly-ledS//2, lx+ledS//2, ly+ledS//2],
                 fill=color, outline=(30,30,30))

# LFO display pocket
draw.rounded_rectangle([670, 393, 800, 508], radius=4, fill=(15,15,15), outline=(40,40,40))
# Waveform (sine)
import math
pts = []
for i in range(100):
    t = i / 99.0
    x = 678 + t * 114
    y = 430 - math.sin(t * 4 * math.pi) * 20
    pts.append((x, y))
draw.line(pts, fill=(255, 96, 48), width=2)
# Labels
draw.text((720, 460), "Sine", fill=(255, 96, 48))
draw.text((715, 478), "2.0 Hz", fill=(255, 96, 48, 180))

# Portrait frame (bottom right)
portrait_path = '/tmp/aether-art/austin-portrait-square.jpg'
if os.path.exists(portrait_path):
    port = Image.open(portrait_path).convert('RGBA').resize((100, 100), Image.LANCZOS)
    bg.paste(port, (880, 480))

out = '/tmp/aether-art/preview_v4.13.png'
bg.save(out)
print(f"Saved: {out}")
