"""
Convert DALL-E knob images into filmstrip PNGs for JUCE.
Each DALL-E image is a knob at 12 o'clock. We:
1. Extract/crop the knob from the 1024x1024 image
2. Rotate it to each of 128 positions (-135° to +135°)
3. Assemble into a horizontal filmstrip (128 frames, 128x128 each)
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os, math

FRAMES = 128
SIZE = 128
START_ANGLE = -135  # leftmost position
END_ANGLE = 135     # rightmost position

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


def extract_knob(img_path):
    """Extract the knob from center of DALL-E image, crop tight, resize to 128x128."""
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    
    # The knob is typically centered. Crop center square (60% of image)
    crop_size = int(min(w, h) * 0.6)
    left = (w - crop_size) // 2
    top = (h - crop_size) // 2
    cropped = img.crop((left, top, left + crop_size, top + crop_size))
    
    # Resize to working size (larger than final for rotation quality)
    work_size = 256
    knob = cropped.resize((work_size, work_size), Image.LANCZOS)
    
    return knob


def make_filmstrip(knob_img, knob_name):
    """Create a 128-frame horizontal filmstrip by rotating the knob."""
    work_size = knob_img.size[0]
    strip = Image.new("RGBA", (FRAMES * SIZE, SIZE), (0, 0, 0, 0))
    
    for f in range(FRAMES):
        t = f / (FRAMES - 1)
        # Angle relative to 12 o'clock (the DALL-E image is at 0°)
        angle = START_ANGLE + t * (END_ANGLE - START_ANGLE)
        
        # Rotate (PIL rotates counter-clockwise, we want clockwise for knob rotation)
        rotated = knob_img.rotate(-angle, resample=Image.BICUBIC, expand=False)
        
        # Resize to final size
        frame = rotated.resize((SIZE, SIZE), Image.LANCZOS)
        
        strip.paste(frame, (f * SIZE, 0))
    
    return strip


for knob_name in KNOBS:
    dalle_path = os.path.join(DALLE_DIR, f"{knob_name}.png")
    if not os.path.exists(dalle_path):
        print(f"MISSING: {dalle_path}")
        continue
    
    print(f"Processing {knob_name}...", end=" ", flush=True)
    
    knob = extract_knob(dalle_path)
    strip = make_filmstrip(knob, knob_name)
    
    out_path = os.path.join(OUT_DIR, f"knob-{knob_name}.png")
    strip.save(out_path)
    print(f"OK -> {out_path}")

print("\nDone! All filmstrips generated.")
