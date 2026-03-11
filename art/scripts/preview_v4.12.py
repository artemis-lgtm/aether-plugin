from PIL import Image, ImageDraw
import os

bg = Image.open('/tmp/aether-plugin/resources/background.png').convert('RGBA')
W, H = bg.size

K = 50
KNOB_POSITIONS = {
    'swellsens': (80, 240), 'swellattack': (160, 240), 'swelldepth': (240, 240),
    'vinylyear': (80, 355), 'vinyldetune': (160, 355),
    'psycheshimmer': (420, 240), 'psychespace': (490, 240), 'psychemod': (560, 240),
    'psychewarp': (630, 240), 'psychemix': (700, 240), 'psychenotches': (770, 240),
    'psychesweep': (840, 240),
    'lfoshape': (455, 410), 'lforate': (525, 410), 'lfodepth': (595, 410),
    'lfosyncrate': (455, 485), 'lfophase': (525, 485),
    'mastermix': (80, 465), 'mastergain': (160, 465),
}

for name, (cx, cy) in KNOB_POSITIONS.items():
    strip_path = f'/tmp/aether-plugin/resources/knob-{name}.png'
    if not os.path.exists(strip_path): continue
    strip = Image.open(strip_path).convert('RGBA')
    frame_size = strip.height
    frame = strip.crop((64 * frame_size, 0, 65 * frame_size, frame_size))
    frame = frame.resize((K, K), Image.LANCZOS)
    bg.paste(frame, (cx - K//2, cy - K//2), frame)

# LFO display pocket
draw = ImageDraw.Draw(bg)
draw.rounded_rectangle([670, 393, 800, 508], radius=4, fill=(15, 15, 15), outline=(60, 60, 60))

# LED dots
leds = [(270, 195), (190, 310), (648, 368), (620, 470), (650, 470)]
psycheStart, psycheGap = 420, 70
leds.append((psycheStart + psycheGap*6 + K//2 + 8, 195))
for lx, ly in leds:
    draw.ellipse([lx-5, ly-5, lx+5, ly+5], fill=(0, 220, 70), outline=(30, 30, 30))

bg.save('/tmp/aether-art/preview_v4.12.png')
print(f"Saved preview ({bg.size})")
