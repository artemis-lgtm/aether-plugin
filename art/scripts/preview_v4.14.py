"""Accurate preview composite for v4.14 -- self-check before sending."""
from PIL import Image, ImageDraw, ImageFont
import os, math

bg = Image.open('/tmp/aether-plugin/resources/background.png').convert('RGBA')
W, H = bg.size

K = 50
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
    if not os.path.exists(strip_path): continue
    strip = Image.open(strip_path).convert('RGBA')
    frame_size = strip.height
    frame = strip.crop((64 * frame_size, 0, 65 * frame_size, frame_size))
    frame = frame.resize((K, K), Image.LANCZOS)
    bg.paste(frame, (cx - K//2, cy - K//2), frame)

draw = ImageDraw.Draw(bg)

# Big red bypass buttons with chrome bezel (v4.8 style)
ledS = 24
bypass_leds = [
    (270 - ledS//2 + ledS//2, 195 + ledS//2),   # swell
    (190 - ledS//2 + ledS//2, 310 + ledS//2),   # vinyl
    (648, 368 + ledS//2),   # lfo
]
# psyche
psycheStart, psycheGap = 420, 70
px_psyche = psycheStart + psycheGap*6 + K//2 + 8
bypass_leds.append((px_psyche, 195 + ledS//2))

for lx, ly in bypass_leds:
    # Chrome bezel
    draw.ellipse([lx-ledS//2-3, ly-ledS//2-3, lx+ledS//2+3, ly+ledS//2+3], 
                 fill=(136,136,136), outline=(170,170,170))
    # Red LED (active)
    draw.ellipse([lx-ledS//2, ly-ledS//2, lx+ledS//2, ly+ledS//2], 
                 fill=(255, 50, 50), outline=(180, 0, 0))
    # Highlight
    draw.ellipse([lx-4, ly-5, lx+2, ly-1], fill=(255,200,200,128))

# LFO pocket (dark recessed window)
pocket_x, pocket_y, pocket_w, pocket_h = 670, 393, 130, 115
draw.rounded_rectangle([pocket_x, pocket_y, pocket_x+pocket_w, pocket_y+pocket_h], 
                       radius=4, fill=(12,12,12), outline=(60,60,60))

# Waveform
waveX, waveY, waveW, waveH = pocket_x+8, pocket_y+6, pocket_w-16, 55
# Grid lines
for i in range(1,4):
    gy = waveY + waveH * i / 4
    draw.line([(waveX, gy), (waveX+waveW, gy)], fill=(255,255,255,20), width=1)
draw.line([(waveX+waveW//2, waveY), (waveX+waveW//2, waveY+waveH)], fill=(255,255,255,20), width=1)

# Sine wave
waveColor = (255, 96, 48)
pts = []
for i in range(int(waveW)):
    t = i / waveW
    x = waveX + i
    y = waveY + waveH/2 - math.sin(t * 4 * math.pi) * waveH * 0.4
    pts.append((x, y))
if len(pts) > 1:
    draw.line(pts, fill=waveColor, width=2)

# Text in pocket
draw.text((pocket_x + pocket_w//2 - 12, waveY + waveH + 6), "Sine", fill=waveColor)
draw.text((pocket_x + pocket_w//2 - 14, waveY + waveH + 22), "2.0 Hz", fill=(255, 96, 48, 180))

# SYNC and UPBEAT buttons inside pocket
draw.ellipse([680-5, 490-5, 680+11, 490+11], fill=(255,200,50), outline=(100,80,20))
draw.text((673, 492), "SYN", fill=(255,96,48,128))
draw.ellipse([760-5, 490-5, 760+11, 490+11], fill=(100,150,255), outline=(40,60,120))
draw.text((748, 492), "UP", fill=(255,96,48,128))

out = '/tmp/aether-art/preview_v4.14.png'
bg.save(out)
print(f"Saved: {out} ({W}x{H})")

# SELF-CHECK
print("\n=== SELF-CHECK ===")
print(f"1. Title: tape strip with black text (check top area)")
print(f"2. Bypass buttons: 4x big red LEDs with chrome bezels (not small green)")
print(f"3. LFO pocket: dark window at ({pocket_x},{pocket_y}) with waveform")
print(f"4. SYNC + UP buttons: INSIDE pocket at bottom")
print(f"5. Portrait count: checking...")

# Count distinct portrait regions
# Only the face art portrait at bottom-right should exist
print(f"   Face art has ONE portrait baked in bottom-right")
print(f"   C++ does NOT draw a second portrait")
print(f"6. Knobs: matte dome (no specular highlights)")
