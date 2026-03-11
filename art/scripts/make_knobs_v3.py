"""
High-quality dome knob filmstrips matching the 3D render.
Smooth plastic dome, subtle specular highlight, dark slot indicator.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import math

FRAMES = 128
SIZE = 128
CENTER = SIZE // 2
RADIUS = 50
START_ANGLE = -135
END_ANGLE = 135

# Colors from the 3D render (more saturated, richer)
SECTIONS = {
    'swell':  (220, 130, 120),  # coral/salmon
    'vinyl':  (120, 200, 140),  # fresh green
    'master': (180, 145, 210),  # rich lavender
    'psyche': (130, 175, 220),  # sky blue
    'lfo':    (220, 195, 110),  # warm gold
}


def make_dome(size, base_rgb):
    """Create a photorealistic dome knob using numpy for smooth gradients."""
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
                # Anti-aliased edge
                alpha = max(0, 1.0 - (dist - 1.0) * 20)
                # Dark edge
                img[y, x] = [r * 0.3, g * 0.3, b * 0.3, alpha * 255]
                continue

            # 3D dome shading using sphere normal
            nz = math.sqrt(max(0, 1.0 - dx * dx - dy * dy))

            # Light direction (top-left, slightly forward)
            lx, ly, lz = -0.35, -0.45, 0.82
            ln = math.sqrt(lx * lx + ly * ly + lz * lz)
            lx, ly, lz = lx / ln, ly / ln, lz / ln

            # Diffuse
            diffuse = max(0, dx * lx + dy * ly + nz * lz)
            diffuse = 0.35 + 0.65 * diffuse  # ambient + diffuse

            # Specular (Phong)
            rx = 2 * nz * dx - lx  # not quite right but close enough
            ry = 2 * nz * dy - ly
            rz = 2 * nz * nz - lz
            spec = max(0, rz / math.sqrt(rx * rx + ry * ry + rz * rz + 0.001))
            spec = spec ** 40 * 0.7  # tight highlight

            # Secondary specular (broader, softer)
            spec2 = max(0, nz) ** 3 * 0.15

            # Edge darkening (Fresnel-like)
            fresnel = (1.0 - nz) ** 2 * 0.3

            # Combine
            cr = min(255, r * diffuse + 255 * spec + 255 * spec2 - r * fresnel)
            cg = min(255, g * diffuse + 255 * spec + 255 * spec2 - g * fresnel)
            cb = min(255, b * diffuse + 255 * spec + 255 * spec2 - b * fresnel)

            img[y, x] = [max(0, cr), max(0, cg), max(0, cb), 255]

    return img


def add_shadow(img_arr, size):
    """Add drop shadow underneath the knob."""
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([CENTER - RADIUS + 2, CENTER - RADIUS + 5,
                CENTER + RADIUS + 2, CENTER + RADIUS + 5],
               fill=(0, 0, 0, 50))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))

    # Convert shadow to array and composite under knob
    sh_arr = np.array(shadow, dtype=np.float32)
    result = sh_arr.copy()

    # Composite knob on top of shadow
    ka = img_arr[:, :, 3:4] / 255.0
    sa = sh_arr[:, :, 3:4] / 255.0
    out_a = ka + sa * (1 - ka)
    out_a_safe = np.maximum(out_a, 0.001)
    result[:, :, :3] = (img_arr[:, :, :3] * ka + sh_arr[:, :, :3] * sa * (1 - ka)) / out_a_safe
    result[:, :, 3:4] = out_a * 255

    return result


def draw_slot(img, angle_deg, size):
    """Draw a dark slot indicator (like a screwdriver slot in a real knob)."""
    pil_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    draw = ImageDraw.Draw(pil_img)
    cx, cy = size / 2, size / 2
    angle_rad = math.radians(angle_deg - 90)

    # Slot: dark recessed line from near-center to near-edge
    slot_start = 8
    slot_end = RADIUS - 6
    sx = cx + slot_start * math.cos(angle_rad)
    sy = cy + slot_start * math.sin(angle_rad)
    ex = cx + slot_end * math.cos(angle_rad)
    ey = cy + slot_end * math.sin(angle_rad)

    # Dark slot (recessed into the dome)
    # Shadow side
    offset = 0.7
    perp_x = -math.sin(angle_rad) * offset
    perp_y = math.cos(angle_rad) * offset
    draw.line([(sx + perp_x, sy + perp_y), (ex + perp_x, ey + perp_y)],
              fill=(0, 0, 0, 80), width=3)
    # Highlight side (opposite)
    draw.line([(sx - perp_x, sy - perp_y), (ex - perp_x, ey - perp_y)],
              fill=(255, 255, 255, 40), width=1)
    # Core slot line
    draw.line([(sx, sy), (ex, ey)], fill=(0, 0, 0, 120), width=2)

    return np.array(pil_img, dtype=np.float32)


def make_filmstrip(section, base_rgb, out_path):
    print(f"  {section}: generating dome...")
    dome = make_dome(SIZE, base_rgb)
    dome = add_shadow(dome, SIZE)

    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))

    for i in range(FRAMES):
        t = i / (FRAMES - 1)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)

        frame = draw_slot(dome.copy(), angle, SIZE)
        frame_img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8), 'RGBA')
        strip.paste(frame_img, (i * SIZE, 0))

    strip.save(out_path)
    print(f"  {section}: {out_path}")


if __name__ == "__main__":
    for name, color in SECTIONS.items():
        make_filmstrip(name, color, f'/tmp/aether-plugin/resources/knob-{name}.png')
    print("Done!")
