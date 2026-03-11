"""
Convert DALL-E knob images into filmstrips.
Each DALL-E image is a 1024x1024 photo of a knob at 12 o'clock.
We need to:
1. Crop/extract the knob from the background
2. Rotate it through 128 frames from -135° to +135°
3. Assemble into a horizontal filmstrip (128 * 128 = 16384 x 128)
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os, math

FRAMES = 128
SIZE = 128  # output frame size
START_ANGLE = -135
END_ANGLE = 135

DALLE_DIR = "/tmp/aether-art/dalle-knobs"
OUT_DIR = "/tmp/aether-plugin/resources"

KNOBS = [
    "swellsens", "swellattack", "swelldepth",
    "vinylyear", "vinyldetune",
    "psycheshimmer", "psychespace", "psychemod", "psychewarp",
    "psychemix", "psychenotches", "psychesweep",
    "lfoshape", "lforate", "lfodepth", "lfosyncrate", "lfophase",
    "mastermix", "mastergain",
]


def extract_knob(img):
    """Extract the knob from its background, center it."""
    # Convert to numpy for analysis
    arr = np.array(img)
    
    # The knob is roughly centered on a dark gray bg
    # Find the knob by looking for non-dark pixels
    gray = np.mean(arr[:, :, :3], axis=2)
    
    # Background is ~42 (dark gray #2A2A2A), knob is brighter
    mask = gray > 60
    
    if not mask.any():
        # Fallback: just use the center region
        cx, cy = img.width // 2, img.height // 2
        r = min(img.width, img.height) // 3
        return img.crop((cx-r, cy-r, cx+r, cy+r))
    
    # Find bounding box of knob
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    
    # Add small padding
    pad = 10
    rmin = max(0, rmin - pad)
    rmax = min(img.height - 1, rmax + pad)
    cmin = max(0, cmin - pad)
    cmax = min(img.width - 1, cmax + pad)
    
    # Make it square (centered)
    h = rmax - rmin
    w = cmax - cmin
    side = max(h, w)
    cx = (cmin + cmax) // 2
    cy = (rmin + rmax) // 2
    
    half = side // 2 + 5
    x1 = max(0, cx - half)
    y1 = max(0, cy - half)
    x2 = min(img.width, cx + half)
    y2 = min(img.height, cy + half)
    
    cropped = img.crop((x1, y1, x2, y2))
    return cropped


def make_filmstrip(knob_img, knob_name):
    """Create a 128-frame filmstrip by rotating the knob image."""
    # Extract and resize to working size
    extracted = extract_knob(knob_img)
    
    # Work at 2x for quality, then downscale
    work_size = SIZE * 3
    knob = extracted.resize((work_size, work_size), Image.LANCZOS)
    
    # Create circular mask to isolate the knob shape
    mask = Image.new("L", (work_size, work_size), 0)
    md = ImageDraw.Draw(mask)
    margin = work_size * 0.08
    md.ellipse([margin, margin, work_size - margin, work_size - margin], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=3))
    
    # Apply mask
    knob_rgba = knob.convert("RGBA")
    knob_rgba.putalpha(mask)
    
    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))
    
    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)
        
        # The DALL-E knob is at 12 o'clock (0°). We need to rotate the whole
        # knob image so the slot indicator moves from -135° to +135°.
        # The slot starts at 0° (top), so we rotate by -angle to make it
        # appear at the right position.
        rotated = knob_rgba.rotate(-angle, resample=Image.BICUBIC, expand=False)
        
        # Downscale to target size
        frame = rotated.resize((SIZE, SIZE), Image.LANCZOS)
        
        # Add subtle drop shadow
        shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        margin_px = int(SIZE * 0.08)
        sd.ellipse([margin_px + 2, margin_px + 4, SIZE - margin_px + 2, SIZE - margin_px + 4],
                   fill=(0, 0, 0, 40))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Composite: shadow behind knob
        composite = Image.alpha_composite(shadow, frame)
        strip.paste(composite, (f * SIZE, 0))
    
    return strip


for knob_name in KNOBS:
    src = os.path.join(DALLE_DIR, f"{knob_name}.png")
    if not os.path.exists(src):
        print(f"MISSING: {src}")
        continue
    
    print(f"Processing {knob_name}...", flush=True)
    img = Image.open(src).convert("RGB")
    strip = make_filmstrip(img, knob_name)
    
    out = os.path.join(OUT_DIR, f"knob-{knob_name}.png")
    strip.save(out)
    print(f"  -> {out} ({strip.size[0]}x{strip.size[1]})")

print("\nDone! All filmstrips generated.")
