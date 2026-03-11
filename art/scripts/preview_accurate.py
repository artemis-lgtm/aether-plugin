"""Most accurate preview possible -- replicates C++ rendering in Python."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, numpy as np

bg = Image.open('/tmp/aether-plugin/resources/background.png').convert('RGBA')
W, H = bg.size  # 1020x620

K = 50

KNOB_POSITIONS = {
    'swellsens': (80, 240), 'swellattack': (160, 240), 'swelldepth': (240, 240),
    'vinylyear': (80, 355), 'vinyldetune': (160, 355),
    'psycheshimmer': (420, 240), 'psychespace': (490, 240), 'psychemod': (560, 240),
    'psychewarp': (630, 240), 'psychemix': (700, 240),
    'psychenotches': (770, 240), 'psychesweep': (840, 240),
    'lfoshape': (455, 410), 'lforate': (525, 410), 'lfodepth': (595, 410),
    'lfosyncrate': (455, 485), 'lfophase': (525, 485),
    'mastermix': (80, 465), 'mastergain': (160, 465),
}

# Paste knobs
for name, (cx, cy) in KNOB_POSITIONS.items():
    strip_path = f'/tmp/aether-plugin/resources/knob-{name}.png'
    if not os.path.exists(strip_path): continue
    strip = Image.open(strip_path).convert('RGBA')
    frame = strip.crop((64 * 128, 0, 65 * 128, 128))
    frame = frame.resize((K, K), Image.LANCZOS)
    bg.paste(frame, (cx - K//2, cy - K//2), frame)

draw = ImageDraw.Draw(bg)

# === BIG RED BYPASS LEDs (replicating C++ BypassLnf) ===
ledS = 24
ledR = ledS * 0.42  # from C++: ledR = min(w,h) * 0.42

bypass_positions = [
    (270, 195 + ledS//2),     # swell
    (190, 310 + ledS//2),     # vinyl
    (648 + ledS//2, 368 + ledS//2),   # lfo
]
# psyche
psycheStart, psycheGap = 420, 70
px_p = psycheStart + psycheGap*6 + K//2 + 8 + ledS//2
bypass_positions.append((px_p, 195 + ledS//2))

for cx, cy in bypass_positions:
    r = ledR
    # Chrome bezel ring (expanded by 3)
    draw.ellipse([cx-r-3, cy-r-3, cx+r+3, cy+r+3], fill=(136,136,136))
    draw.ellipse([cx-r-3, cy-r-3, cx+r+3, cy+r+3], outline=(170,170,170), width=2)
    draw.ellipse([cx-r-1.5, cy-r-1.5, cx+r+1.5, cy+r+1.5], outline=(85,85,85), width=1)
    
    # Outer glow
    glow = Image.new('RGBA', (int(r*5), int(r*5)), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gc = r*2.5
    gd.ellipse([gc-r*2, gc-r*2, gc+r*2, gc+r*2], fill=(255,16,16,37))
    gd.ellipse([gc-r*1.2, gc-r*1.2, gc+r*1.2, gc+r*1.2], fill=(255,32,32,64))
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    bg.paste(glow, (int(cx-gc), int(cy-gc)), glow)
    draw = ImageDraw.Draw(bg)  # refresh after paste
    
    # Bright red LED body (gradient effect)
    for i in range(int(r), 0, -1):
        t = i / r
        red = int(255 - (255-187) * t * t)
        green = int(64 * (1 - t*t))
        draw.ellipse([cx-i, cy-i, cx+i, cy+i], fill=(red, green, 0))
    
    # Hot spot highlight
    draw.ellipse([cx-r*0.35, cy-r*0.4, cx+r*0.15, cy-r*0.05], fill=(255,180,180,128))
    
    # Glass dome edge
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(0,0,0,48), width=1)

# === LFO POCKET (replicating drawLfoPocket) ===
px, py, pw, ph = 670, 393, 130, 115
corner_r = 4

# Outer shadow
draw.rounded_rectangle([px-1, py-1, px+pw+1, py+ph+1], radius=corner_r+1, outline=(0,0,0,96), width=2)

# Dark background gradient
draw.rounded_rectangle([px, py, px+pw, py+ph], radius=corner_r, fill=(14,14,12))

# Inner bevel (top-left dark, bottom-right light)
draw.line([(px+1, py+1), (px+pw-1, py+1)], fill=(0,0,0,64), width=2)
draw.line([(px+1, py+1), (px+1, py+ph-1)], fill=(0,0,0,64), width=2)
draw.line([(px+2, py+ph-1), (px+pw-1, py+ph-1)], fill=(255,255,255,24), width=1)
draw.line([(px+pw-1, py+2), (px+pw-1, py+ph-1)], fill=(255,255,255,24), width=1)

# Waveform area
waveX, waveY = px + 8, py + 6
waveW, waveH = pw - 16, 55

# Grid lines
for i in range(1, 4):
    gy = int(waveY + waveH * i / 4)
    draw.line([(waveX, gy), (waveX+waveW, gy)], fill=(255,255,255,21), width=1)
draw.line([(int(waveX+waveW*0.5), waveY), (int(waveX+waveW*0.5), waveY+waveH)], fill=(255,255,255,21), width=1)

# Sine waveform (warm amber)
waveColor = (255, 96, 48)
pts = []
for i in range(int(waveW)):
    t = i / waveW
    x = waveX + i
    y = waveY + waveH/2 - math.sin(t * 4 * math.pi) * waveH * 0.4
    pts.append((x, y))

# Glow under waveform
glow_pts = [(int(x), int(y)) for x, y in pts]
if len(glow_pts) > 1:
    draw.line(glow_pts, fill=(255, 96, 48, 38), width=6)
    draw.line(glow_pts, fill=(255, 96, 48, 77), width=3)
    draw.line(glow_pts, fill=waveColor, width=2)

# Text below waveform
textY = waveY + waveH + 6
draw.text((int(waveX + waveW/2 - 12), int(textY)), "Sine", fill=waveColor)
draw.text((int(waveX + waveW/2 - 16), int(textY + 16)), "2.0 Hz", fill=(255, 96, 48, 180))

# SYNC button inside pocket (small amber circle)
syn_x, syn_y = 688, 498
draw.ellipse([syn_x-6, syn_y-6, syn_x+6, syn_y+6], fill=(200,160,40), outline=(100,80,20))
draw.text((syn_x-12, syn_y-18), "SYN", fill=(255,96,48,128))

# UPBEAT button inside pocket
up_x, up_y = 768, 498
draw.ellipse([up_x-6, up_y-6, up_x+6, up_y+6], fill=(80,120,220), outline=(40,60,120))
draw.text((up_x-8, up_y-18), "UP", fill=(255,96,48,128))

out = '/tmp/aether-art/preview_v4.14_accurate.png'
bg.save(out)
print(f"Saved: {out}")
