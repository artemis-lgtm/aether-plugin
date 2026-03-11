"""
Generate per-KNOB filmstrips: MATTE finish, SHARP/FACETED edges.
Like hex bolt heads or faceted guitar pedal knobs -- flat top with angular beveled edges.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import math, random, os

FRAMES = 128
SIZE = 128
CENTER = SIZE // 2
RADIUS = 48
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

NUM_SIDES = 6  # hexagonal faceted knob


def make_faceted_knob(size, base_rgb):
    """Create a flat-topped hexagonal knob with matte finish and sharp beveled edges."""
    img = np.zeros((size, size, 4), dtype=np.float32)
    cx, cy = size / 2.0, size / 2.0
    r, g, b = base_rgb

    # Desaturate slightly for matte look
    avg = (r + g + b) / 3.0
    mr = r * 0.8 + avg * 0.2
    mg = g * 0.8 + avg * 0.2
    mb = b * 0.8 + avg * 0.2

    for y in range(size):
        for x in range(size):
            dx = (x - cx) / RADIUS
            dy = (y - cy) / RADIUS

            # Hexagonal distance (sharp edges)
            angle = math.atan2(dy, dx)
            hex_dist = math.sqrt(dx * dx + dy * dy)

            # Hexagonal shape factor
            sector = angle + math.pi  # 0 to 2pi
            sector_angle = (sector % (math.pi * 2 / NUM_SIDES)) - (math.pi / NUM_SIDES)
            hex_factor = math.cos(math.pi / NUM_SIDES) / max(math.cos(sector_angle), 0.001)
            norm_dist = hex_dist / hex_factor

            if norm_dist > 1.08:
                continue

            # Sharp edge with small anti-alias band
            if norm_dist > 1.0:
                alpha = max(0, 1.0 - (norm_dist - 1.0) * 12.5)
                edge_dark = 0.35
                img[y, x] = [mr * edge_dark, mg * edge_dark, mb * edge_dark, alpha * 255]
                continue

            # === MATTE lighting model ===
            # Light from upper-left
            lx, ly, lz = -0.4, -0.5, 0.75
            ln = math.sqrt(lx*lx + ly*ly + lz*lz)
            lx, ly, lz = lx/ln, ly/ln, lz/ln

            # Flat top with sharp bevel at edges
            bevel_start = 0.82
            if norm_dist < bevel_start:
                # Flat top: normal points straight up
                nx, ny, nz = 0.0, 0.0, 1.0
            else:
                # Beveled edge: normal points outward
                bevel_t = (norm_dist - bevel_start) / (1.0 - bevel_start)
                edge_nx = dx / max(hex_dist, 0.001)
                edge_ny = dy / max(hex_dist, 0.001)
                nz = 1.0 - bevel_t * 0.9
                nx = edge_nx * bevel_t * 0.9
                ny = edge_ny * bevel_t * 0.9
                nm = math.sqrt(nx*nx + ny*ny + nz*nz)
                nx, ny, nz = nx/nm, ny/nm, nz/nm

            # Diffuse only (matte = no specular)
            diffuse = max(0, nx*lx + ny*ly + nz*lz)
            diffuse = 0.30 + 0.70 * diffuse

            # Very subtle ambient occlusion at edges
            ao = 1.0 - max(0, norm_dist - 0.7) * 0.3

            # No specular (matte), no fresnel
            cr = min(255, mr * diffuse * ao)
            cg = min(255, mg * diffuse * ao)
            cb = min(255, mb * diffuse * ao)
            img[y, x] = [max(0, cr), max(0, cg), max(0, cb), 255]

    return img


def add_shadow(img_arr, size):
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([CENTER-RADIUS+3, CENTER-RADIUS+6, CENTER+RADIUS+3, CENTER+RADIUS+6],
               fill=(0, 0, 0, 45))
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


def draw_pointer(img, angle_deg, size):
    """Draw a clear white pointer line with dark shadow for matte knobs."""
    pil_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(pil_img)
    cx, cy = size/2, size/2
    angle_rad = math.radians(angle_deg - 90)

    slot_start = 8
    slot_end = RADIUS - 5
    sx = cx + slot_start * math.cos(angle_rad)
    sy = cy + slot_start * math.sin(angle_rad)
    ex = cx + slot_end * math.cos(angle_rad)
    ey = cy + slot_end * math.sin(angle_rad)

    # Dark groove (shadow)
    draw.line([(sx+1, sy+1), (ex+1, ey+1)], fill=(0, 0, 0, 220), width=5)
    # White pointer
    draw.line([(sx, sy), (ex, ey)], fill=(255, 255, 255, 255), width=3)
    # Bright tip dot
    draw.ellipse([ex-3, ey-3, ex+3, ey+3], fill=(255, 255, 255, 255))

    return np.array(pil_img, dtype=np.float32)


OUT_DIR = '/tmp/aether-plugin/resources'
os.makedirs(OUT_DIR, exist_ok=True)

for i, knob_name in enumerate(KNOBS):
    color = PALETTE[i % len(PALETTE)]
    print(f"{knob_name}: {color}...")

    dome = make_faceted_knob(SIZE, color)
    dome = add_shadow(dome, SIZE)

    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))

    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)
        frame_arr = draw_pointer(dome.copy(), angle, SIZE)
        frame_img = Image.fromarray(np.clip(frame_arr, 0, 255).astype(np.uint8), 'RGBA')
        strip.paste(frame_img, (f * SIZE, 0))

    fname = knob_name.replace('-', '')
    out = os.path.join(OUT_DIR, f'knob-{fname}.png')
    strip.save(out)
    print(f"    -> {out}")

print("Done!")
