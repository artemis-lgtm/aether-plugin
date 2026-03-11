"""
Generate per-section colored dome knob filmstrips with visible indicator.
128 frames, 128x128 each, horizontal strip = 16384x128.
Knob: smooth dome with highlight, clear white indicator line from center to edge.
"""
from PIL import Image, ImageDraw, ImageFilter
import math, os

FRAMES = 128
SIZE = 128
CENTER = SIZE // 2
RADIUS = 52  # knob radius in pixels
INDICATOR_LEN = 42  # from center outward
START_ANGLE = -135  # degrees (7 o'clock position)
END_ANGLE = 135     # degrees (5 o'clock position, 270° sweep)

# Section colors: (base_r, base_g, base_b) for the dome
SECTIONS = {
    'swell':  (210, 140, 130),  # warm pink-red
    'vinyl':  (140, 195, 145),  # soft green
    'master': (175, 150, 195),  # light purple
    'psyche': (140, 170, 210),  # soft blue
    'lfo':    (210, 195, 130),  # warm gold
}

def make_knob_frame(base_color, angle_deg, size=SIZE):
    """Draw one knob frame at a given angle."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    
    # Shadow under knob
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([cx - RADIUS - 2, cy - RADIUS + 3, cx + RADIUS + 2, cy + RADIUS + 7],
               fill=(0, 0, 0, 60))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    img = Image.alpha_composite(img, shadow)
    draw = ImageDraw.Draw(img)
    
    # Base dome circle
    r, g, b = base_color
    draw.ellipse([cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS],
                 fill=(r, g, b, 255))
    
    # 3D dome highlight: lighter top-left, darker bottom-right
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    # Top-left bright spot
    for i in range(20, 0, -1):
        alpha = int(80 * (1 - i / 20))
        offset = int(RADIUS * 0.25)
        hr = int(RADIUS * 0.3 + i * 1.5)
        hd.ellipse([cx - offset - hr, cy - offset - hr,
                     cx - offset + hr, cy - offset + hr],
                    fill=(255, 255, 255, alpha))
    highlight = highlight.filter(ImageFilter.GaussianBlur(radius=8))
    
    # Apply highlight only inside knob circle
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS], fill=255)
    highlight.putalpha(Image.composite(highlight.split()[3], Image.new("L", (size, size), 0), mask))
    img = Image.alpha_composite(img, highlight)
    
    # Bottom-right shadow on dome
    dome_shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dsd = ImageDraw.Draw(dome_shadow)
    for i in range(15, 0, -1):
        alpha = int(40 * (1 - i / 15))
        offset = int(RADIUS * 0.3)
        hr = int(RADIUS * 0.4 + i * 1.2)
        dsd.ellipse([cx + offset - hr, cy + offset - hr,
                      cx + offset + hr, cy + offset + hr],
                     fill=(0, 0, 0, alpha))
    dome_shadow = dome_shadow.filter(ImageFilter.GaussianBlur(radius=6))
    dome_shadow.putalpha(Image.composite(dome_shadow.split()[3], Image.new("L", (size, size), 0), mask))
    img = Image.alpha_composite(img, dome_shadow)
    
    # Subtle edge ring
    draw = ImageDraw.Draw(img)
    draw.ellipse([cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS],
                 outline=(0, 0, 0, 40), width=1)
    draw.ellipse([cx - RADIUS + 1, cy - RADIUS + 1, cx + RADIUS - 1, cy + RADIUS - 1],
                 outline=(255, 255, 255, 25), width=1)
    
    # Indicator line: bright white with dark outline
    angle_rad = math.radians(angle_deg - 90)  # -90 because 0° = up
    end_x = cx + INDICATOR_LEN * math.cos(angle_rad)
    end_y = cy + INDICATOR_LEN * math.sin(angle_rad)
    start_x = cx + 6 * math.cos(angle_rad)  # start slightly from center
    start_y = cy + 6 * math.sin(angle_rad)
    
    # Dark outline for indicator
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            draw.line([(start_x + dx, start_y + dy), (end_x + dx, end_y + dy)],
                      fill=(0, 0, 0, 120), width=3)
    
    # Bright white indicator
    draw.line([(start_x, start_y), (end_x, end_y)],
              fill=(255, 255, 255, 240), width=2)
    
    # Small bright dot at indicator tip
    draw.ellipse([end_x - 2, end_y - 2, end_x + 2, end_y + 2],
                 fill=(255, 255, 255, 200))
    
    return img


def make_filmstrip(section_name, base_color, out_path):
    """Generate 128-frame horizontal filmstrip."""
    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))
    
    for i in range(FRAMES):
        t = i / (FRAMES - 1)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)
        frame = make_knob_frame(base_color, angle)
        strip.paste(frame, (i * SIZE, 0))
    
    strip.save(out_path)
    print(f"  {section_name}: {out_path} ({strip.size[0]}x{strip.size[1]})")


if __name__ == "__main__":
    out_dir = "/tmp/aether-plugin/resources"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Generating knob filmstrips...")
    for name, color in SECTIONS.items():
        make_filmstrip(name, color, f"{out_dir}/knob-{name}.png")
    print("Done!")
