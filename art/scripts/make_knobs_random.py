"""
Generate per-KNOB colored dome filmstrips with random colors.
19 knobs, each gets a unique random color from a vibrant palette.
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

# Vibrant palette matching the render (randomized per knob)
PALETTE = [
    (220, 100, 100),  # red-coral
    (230, 140, 110),  # peach
    (220, 170, 90),   # gold
    (200, 200, 100),  # lime-gold
    (110, 200, 130),  # green
    (90, 190, 180),   # teal
    (110, 170, 220),  # sky blue
    (140, 140, 220),  # periwinkle
    (180, 130, 210),  # lavender
    (210, 120, 170),  # pink
    (230, 130, 130),  # salmon
    (170, 210, 130),  # light green
    (130, 200, 200),  # cyan
    (200, 150, 120),  # tan
    (160, 180, 210),  # steel blue
    (210, 160, 190),  # rose
    (180, 200, 140),  # sage
    (220, 180, 140),  # warm sand
    (150, 170, 200),  # dusty blue
]

# All 19 knobs with their names
KNOBS = [
    'swell-sens', 'swell-attack', 'swell-depth',
    'vinyl-year', 'vinyl-detune',
    'psyche-shimmer', 'psyche-space', 'psyche-mod', 'psyche-warp',
    'psyche-mix', 'psyche-notches', 'psyche-sweep',
    'lfo-shape', 'lfo-rate', 'lfo-depth', 'lfo-syncrate', 'lfo-phase',
    'master-mix', 'master-gain',
]

random.seed(42)  # reproducible but random-looking
random.shuffle(PALETTE)


def make_dome(size, base_rgb):
    img = np.zeros((size, size, 4), dtype=np.float32)
    cx, cy = size / 2, size / 2
    r, g, b = base_rgb

    for y in range(size):
        for x in range(size):
            dx = (x - cx) / RADIUS
            dy = (y - cy) / RADIUS
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > 1.05:
                continue
            if dist > 1.0:
                alpha = max(0, 1.0 - (dist - 1.0) * 20)
                img[y, x] = [r * 0.3, g * 0.3, b * 0.3, alpha * 255]
                continue

            nz = math.sqrt(max(0, 1.0 - dx * dx - dy * dy))
            lx, ly, lz = -0.35, -0.45, 0.82
            ln = math.sqrt(lx*lx + ly*ly + lz*lz)
            lx, ly, lz = lx/ln, ly/ln, lz/ln

            diffuse = max(0, dx*lx + dy*ly + nz*lz)
            diffuse = 0.35 + 0.65 * diffuse

            rz = 2*nz*nz - lz
            rx = 2*nz*dx - lx
            ry = 2*nz*dy - ly
            spec = max(0, rz / math.sqrt(rx*rx + ry*ry + rz*rz + 0.001))
            spec = spec ** 40 * 0.7
            spec2 = max(0, nz) ** 3 * 0.15
            fresnel = (1.0 - nz) ** 2 * 0.3

            cr = min(255, r*diffuse + 255*spec + 255*spec2 - r*fresnel)
            cg = min(255, g*diffuse + 255*spec + 255*spec2 - g*fresnel)
            cb = min(255, b*diffuse + 255*spec + 255*spec2 - b*fresnel)
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
    pil_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(pil_img)
    cx, cy = size/2, size/2
    angle_rad = math.radians(angle_deg - 90)
    slot_start = 8
    slot_end = RADIUS - 6
    sx = cx + slot_start * math.cos(angle_rad)
    sy = cy + slot_start * math.sin(angle_rad)
    ex = cx + slot_end * math.cos(angle_rad)
    ey = cy + slot_end * math.sin(angle_rad)
    offset = 0.7
    perp_x = -math.sin(angle_rad) * offset
    perp_y = math.cos(angle_rad) * offset
    draw.line([(sx+perp_x, sy+perp_y), (ex+perp_x, ey+perp_y)], fill=(0,0,0,80), width=3)
    draw.line([(sx-perp_x, sy-perp_y), (ex-perp_x, ey-perp_y)], fill=(255,255,255,40), width=1)
    draw.line([(sx, sy), (ex, ey)], fill=(0,0,0,120), width=2)
    return np.array(pil_img, dtype=np.float32)


# Generate all 19 knob filmstrips
out_dir = '/tmp/aether-plugin/resources'
os.makedirs(out_dir, exist_ok=True)

for idx, knob_name in enumerate(KNOBS):
    color = PALETTE[idx % len(PALETTE)]
    print(f"  {knob_name}: {color}...")
    dome = make_dome(SIZE, color)
    dome = add_shadow(dome, SIZE)

    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))
    for i in range(FRAMES):
        t = i / (FRAMES - 1)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)
        frame = draw_slot(dome.copy(), angle, SIZE)
        frame_img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8), 'RGBA')
        strip.paste(frame_img, (i * SIZE, 0))

    safe_name = knob_name.replace('-', '')
    strip.save(f'{out_dir}/knob-{safe_name}.png')
    print(f"    -> knob-{safe_name}.png")

print("Done! 19 random-color knob filmstrips.")
