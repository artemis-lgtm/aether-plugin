"""
Overlay visible indicator lines on Blender-rendered knob frames.
Takes the realistic 3D frames and adds a clear white slot indicator.
"""
from PIL import Image, ImageDraw
import math, os

FRAMES = 128
SIZE = 128
CENTER = SIZE // 2
INDICATOR_LEN = 38  # from center to near edge
START_ANGLE = -135   # 7 o'clock
END_ANGLE = 135      # 5 o'clock

SECTIONS = ['swell', 'vinyl', 'master', 'psyche', 'lfo']

def add_indicator(frame, angle_deg):
    """Add a white indicator line to a knob frame."""
    draw = ImageDraw.Draw(frame)
    cx, cy = CENTER, CENTER
    angle_rad = math.radians(angle_deg - 90)  # -90 so 0° = up
    
    start_x = cx + 5 * math.cos(angle_rad)
    start_y = cy + 5 * math.sin(angle_rad)
    end_x = cx + INDICATOR_LEN * math.cos(angle_rad)
    end_y = cy + INDICATOR_LEN * math.sin(angle_rad)
    
    # Dark outline
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx != 0 or dy != 0:
                draw.line([(start_x+dx, start_y+dy), (end_x+dx, end_y+dy)],
                          fill=(0, 0, 0, 100), width=3)
    
    # White indicator line
    draw.line([(start_x, start_y), (end_x, end_y)],
              fill=(255, 255, 255, 230), width=2)
    
    # Bright tip dot
    draw.ellipse([end_x-2.5, end_y-2.5, end_x+2.5, end_y+2.5],
                 fill=(255, 255, 255, 200))
    
    return frame


for section in SECTIONS:
    frame_dir = f'/tmp/aether-art/knob-frames-{section}'
    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))
    
    for i in range(FRAMES):
        t = i / (FRAMES - 1)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)
        
        frame = Image.open(f'{frame_dir}/frame_{i:03d}.png').copy()
        frame = add_indicator(frame, angle)
        strip.paste(frame, (i * SIZE, 0))
    
    out = f'/tmp/aether-plugin/resources/knob-{section}.png'
    strip.save(out)
    print(f'{section}: saved {out}')

print("Done -- Blender knobs with indicators!")
