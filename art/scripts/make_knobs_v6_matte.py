"""
Generate per-KNOB colored dome filmstrips with CLEARLY VISIBLE rotation indicator.
The slot/pointer must be obvious at plugin size (~50px knobs).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import math, random, os

FRAMES = 128
SIZE = 128
CENTER = SIZE // 2
RADIUS = 50
START_ANGLE = -135
END_ANGLE = 135

PALETTE = [
    (220, 100, 100), (230, 140, 110), (220, 170, 90), (200, 200, 100),
    (110, 200, 130), (90, 190, 180), (110, 170, 220), (140, 140, 220),
    (180, 130, 210), (210, 120, 170), (230, 130, 130), (170, 210, 130),
    (130, 200, 200), (200, 150, 120), (160, 180, 210), (210, 160, 190),
    (180, 200, 140), (220, 180, 140), (150, 170, 200),
]

KNOBS = [
    'swell-sens', 'swell-attack', 'swell-depth',
    'vinyl-year', 'vinyl-detune',
    'psyche-shimmer', 'psyche-space', 'psyche-mod', 'psyche-warp',
    'psyche-mix', 'psyche-notches', 'psyche-sweep',
    'lfo-shape', 'lfo-rate', 'lfo-depth', 'lfo-syncrate', 'lfo-phase',
    'master-mix', 'master-gain',
]

random.seed(42)
random.shuffle(PALETTE)


def make_dome(size, base_rgb):
    img = np.zeros((size, size, 4), dtype=np.float32)
    cx, cy = size / 2, size / 2
    r, g, b = base_rgb
    for y in range(size):
        for x in range(size):
            dx = (x - cx) / RADIUS
            dy = (y - cy) / RADIUS
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 1.05: continue
            if dist > 1.0:
                alpha = max(0, 1.0 - (dist - 1.0) * 20)
                img[y, x] = [r*0.3, g*0.3, b*0.3, alpha*255]
                continue
            nz = math.sqrt(max(0, 1.0 - dx*dx - dy*dy))
            lx, ly, lz = -0.35, -0.45, 0.82
            ln = math.sqrt(lx*lx + ly*ly + lz*lz)
            lx, ly, lz = lx/ln, ly/ln, lz/ln
            diffuse = max(0, dx*lx + dy*ly + nz*lz)
            diffuse = 0.30 + 0.70 * diffuse
            # MATTE: no specular, no fresnel -- pure diffuse lighting
            cr = min(255, r*diffuse)
            cg = min(255, g*diffuse)
            cb = min(255, b*diffuse)
            img[y, x] = [max(0, cr), max(0, cg), max(0, cb), 255]
    return img


def add_shadow(img_arr, size):
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([CENTER-RADIUS+2, CENTER-RADIUS+5, CENTER+RADIUS+2, CENTER+RADIUS+5],
               fill=(0, 0, 0, 50))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
    sh_arr = np.array(shadow, dtype=np.float32)
    result = sh_arr.copy()
    ka = img_arr[:, :, 3:4] / 255.0
    sa = sh_arr[:, :, 3:4] / 255.0
    out_a = ka + sa * (1 - ka)
    out_a_safe = np.maximum(out_a, 0.001)
    result[:, :, :3] = (img_arr[:, :, :3]*ka + sh_arr[:, :, :3]*sa*(1 - ka)) / out_a_safe
    result[:, :, 3:4] = out_a * 255
    return result


def draw_slot(img, angle_deg, size):
    """Draw a THICK, HIGH-CONTRAST pointer line that's clearly visible at 50px."""
    pil_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(pil_img)
    cx, cy = size/2, size/2
    angle_rad = math.radians(angle_deg - 90)
    
    # Pointer from near center to near edge of dome
    slot_start = 10
    slot_end = RADIUS - 3
    sx = cx + slot_start * math.cos(angle_rad)
    sy = cy + slot_start * math.sin(angle_rad)
    ex = cx + slot_end * math.cos(angle_rad)
    ey = cy + slot_end * math.sin(angle_rad)
    
    # Dark shadow line (offset slightly)
    draw.line([(sx+1, sy+1), (ex+1, ey+1)], fill=(0, 0, 0, 200), width=5)
    # White bright pointer line - THICK and OPAQUE
    draw.line([(sx, sy), (ex, ey)], fill=(255, 255, 255, 255), width=3)
    # Bright dot at the tip
    draw.ellipse([ex-3, ey-3, ex+3, ey+3], fill=(255, 255, 255, 255))
    
    return np.array(pil_img, dtype=np.float32)


OUT_DIR = '/tmp/aether-plugin/resources'
os.makedirs(OUT_DIR, exist_ok=True)

for i, knob_name in enumerate(KNOBS):
    color = PALETTE[i % len(PALETTE)]
    print(f"{knob_name}: {color}...")
    
    dome = make_dome(SIZE, color)
    dome = add_shadow(dome, SIZE)
    
    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))
    
    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)
        frame_arr = draw_slot(dome.copy(), angle, SIZE)
        frame_img = Image.fromarray(np.clip(frame_arr, 0, 255).astype(np.uint8), 'RGBA')
        strip.paste(frame_img, (f * SIZE, 0))
    
    fname = knob_name.replace('-', '')
    out = os.path.join(OUT_DIR, f'knob-{fname}.png')
    strip.save(out)
    print(f"    -> {out}")

print("Done!")
