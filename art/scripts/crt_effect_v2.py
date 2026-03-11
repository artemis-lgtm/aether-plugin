"""
CRT effect v2 -- MSEVEN-quality.
Core principle: CRT is ADDITIVE (phosphors glow in darkness).
The image should feel like it's emitting light, not filtered.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import math

def apply_crt_v2(portrait_path, output_path, size=(400, 400)):
    """MSEVEN-quality CRT effect."""
    
    img = Image.open(portrait_path).convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    w, h = img.size
    
    # === STEP 1: Color grading (warm, vivid CRT phosphors) ===
    # Boost saturation heavily
    img = ImageEnhance.Color(img).enhance(1.8)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img = ImageEnhance.Brightness(img).enhance(1.15)
    
    arr = np.array(img).astype(np.float32)
    
    # Warm shift: boost reds/greens slightly, CRT phosphor warmth
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.1, 0, 255)   # red boost
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.05, 0, 255)   # slight green
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.9, 0, 255)    # reduce blue
    
    # === STEP 2: Barrel distortion (CRT screen curvature) ===
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w/2.0, h/2.0
    nx = (xx - cx) / cx
    ny = (yy - cy) / cy
    r2 = nx**2 + ny**2
    strength = 0.12
    factor = 1 + strength * r2
    sx = (cx + nx * factor * cx).astype(int)
    sy = (cy + ny * factor * cy).astype(int)
    
    # Pixels outside bounds -> black (like CRT border)
    valid = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    distorted = np.zeros_like(arr)
    distorted[valid] = arr[sy[valid], sx[valid]]
    
    # === STEP 3: RGB Chromatic Aberration (horizontal misregistration) ===
    shift = 3
    result = np.zeros_like(distorted)
    result[:, shift:, 0] = distorted[:, :-shift, 0]    # Red shifted right
    result[:, :, 1] = distorted[:, :, 1]                 # Green center
    result[:, :-shift, 2] = distorted[:, shift:, 2]     # Blue shifted left
    
    # === STEP 4: RGB Phosphor Subpixel Pattern ===
    # Real CRT: each pixel is 3 vertical phosphor stripes (R, G, B)
    # Create phosphor mask
    phosphor = np.zeros((h, w, 3), dtype=np.float32)
    for x in range(w):
        col_type = x % 3
        if col_type == 0:    # Red phosphor column
            phosphor[:, x, 0] = 1.0
            phosphor[:, x, 1] = 0.15
            phosphor[:, x, 2] = 0.15
        elif col_type == 1:  # Green phosphor column
            phosphor[:, x, 0] = 0.15
            phosphor[:, x, 1] = 1.0
            phosphor[:, x, 2] = 0.15
        else:                # Blue phosphor column
            phosphor[:, x, 0] = 0.15
            phosphor[:, x, 1] = 0.15
            phosphor[:, x, 2] = 1.0
    
    # Apply phosphor pattern
    phosphored = result * phosphor
    
    # === STEP 5: Scanlines (horizontal gaps between pixel rows) ===
    scanline_mask = np.ones((h, w), dtype=np.float32)
    scan_period = 4  # period in pixels
    for y in range(h):
        phase = y % scan_period
        if phase == 0:
            scanline_mask[y, :] = 1.0    # Bright phosphor row
        elif phase == 1:
            scanline_mask[y, :] = 0.85   # Still bright
        elif phase == 2:
            scanline_mask[y, :] = 0.25   # Gap between rows (dark)
        else:
            scanline_mask[y, :] = 0.5    # Transition
    
    for c in range(3):
        phosphored[:, :, c] *= scanline_mask
    
    # === STEP 6: Phosphor Bloom / Glow (THIS IS KEY) ===
    # Bright phosphors bleed light into neighboring pixels
    # This makes it look like it's EMITTING light
    
    # Create bloom from the original bright image (pre-scanline)
    bloom_src = result.copy()
    bloom_src = np.clip(bloom_src, 0, 255).astype(np.uint8)
    bloom_img = Image.fromarray(bloom_src)
    
    # Multi-pass bloom at different scales
    bloom1 = bloom_img.filter(ImageFilter.GaussianBlur(radius=4))
    bloom2 = bloom_img.filter(ImageFilter.GaussianBlur(radius=12))
    bloom3 = bloom_img.filter(ImageFilter.GaussianBlur(radius=25))
    
    b1 = np.array(bloom1).astype(np.float32)
    b2 = np.array(bloom2).astype(np.float32)
    b3 = np.array(bloom3).astype(np.float32)
    
    # Additive bloom (THIS is what makes CRT look like it glows)
    final = phosphored.copy()
    final += b1 * 0.3   # tight glow
    final += b2 * 0.15  # medium bloom
    final += b3 * 0.08  # wide halo
    
    # === STEP 7: Vignette (CRT is darker at edges due to curved glass) ===
    vig = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            d = math.sqrt(dx**2 + dy**2)
            # Smooth falloff from center
            vig[y, x] = max(0, 1.0 - 0.4 * d**2)
    
    for c in range(3):
        final[:, :, c] *= vig
    
    # === STEP 8: Noise/static ===
    noise = np.random.normal(0, 5, final.shape)
    final += noise
    
    # === STEP 9: Screen reflection / glass sheen ===
    # Subtle diagonal highlight across the glass
    sheen = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            # Diagonal from top-left
            t = (x / w + y / h) / 2
            # Gaussian peak around 0.3
            sheen[y, x] = math.exp(-(t - 0.3)**2 / 0.02) * 25
    
    for c in range(3):
        final[:, :, c] += sheen
    
    # Clamp and convert
    final = np.clip(final, 0, 255).astype(np.uint8)
    img_out = Image.fromarray(final)
    
    # === STEP 10: Rounded corners (CRT screen shape) ===
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    corner_r = int(min(w, h) * 0.08)
    md.rounded_rectangle([0, 0, w-1, h-1], radius=corner_r, fill=255)
    
    # Feather the edge slightly
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Black background
    bg = Image.new('RGB', (w, h), (2, 2, 2))
    bg.paste(img_out, mask=mask)
    
    bg.save(output_path)
    print(f"Saved CRT v2: {output_path} ({w}x{h})")

# Generate at inspection size
apply_crt_v2("/tmp/aether-art/austin-portrait-square.jpg", 
             "/tmp/aether-art/crt_portrait_v2_large.png", size=(400, 400))

# Generate at plugin size
apply_crt_v2("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v2.png", size=(175, 175))
