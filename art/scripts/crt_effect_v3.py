"""
CRT effect v3 -- BLOOM IS KING.
The MSEVEN look = photographing a real CRT in a dark room.
Bright phosphors bleed massive soft light into surrounding darkness.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import math

def apply_crt_v3(portrait_path, output_path, size=(400, 400)):
    img = Image.open(portrait_path).convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    w, h = img.size
    cx, cy = w/2.0, h/2.0
    
    # === STEP 1: Color grading -- warm, vivid, high contrast ===
    img = ImageEnhance.Color(img).enhance(2.0)       # very saturated
    img = ImageEnhance.Contrast(img).enhance(1.6)     # high contrast
    img = ImageEnhance.Brightness(img).enhance(1.2)   # brighter
    
    arr = np.array(img).astype(np.float32)
    
    # Warm shift: amber/gold highlights
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.15, 0, 255)  # red warm
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.05, 0, 255)  # slight green
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.8, 0, 255)   # reduce blue more
    
    # === STEP 2: Pre-blur (CRT electron beam doesn't resolve sharp detail) ===
    soft = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    soft = soft.filter(ImageFilter.GaussianBlur(radius=1.5))
    arr = np.array(soft).astype(np.float32)
    
    # === STEP 3: Barrel distortion ===
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - cx) / cx
    ny = (yy - cy) / cy
    r2 = nx**2 + ny**2
    strength = 0.18  # stronger curvature
    factor = 1 + strength * r2
    sx = (cx + nx * factor * cx).astype(int)
    sy = (cy + ny * factor * cy).astype(int)
    valid = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    distorted = np.zeros_like(arr)
    distorted[valid] = arr[sy[valid], sx[valid]]
    
    # === STEP 4: RGB Chromatic Aberration ===
    shift = 3
    aberrated = np.zeros_like(distorted)
    aberrated[:, shift:, 0] = distorted[:, :-shift, 0]
    aberrated[:, :, 1] = distorted[:, :, 1]
    aberrated[:, :-shift, 2] = distorted[:, shift:, 2]
    
    # === STEP 5: Create BLOOM first (before scanlines destroy brightness) ===
    # This is the key to the MSEVEN look
    bloom_src = np.clip(aberrated, 0, 255).astype(np.uint8)
    bloom_img = Image.fromarray(bloom_src)
    
    # Multi-scale bloom (each scale adds softer, wider glow)
    bloom_tight = np.array(bloom_img.filter(ImageFilter.GaussianBlur(radius=6))).astype(np.float32)
    bloom_med = np.array(bloom_img.filter(ImageFilter.GaussianBlur(radius=18))).astype(np.float32)
    bloom_wide = np.array(bloom_img.filter(ImageFilter.GaussianBlur(radius=40))).astype(np.float32)
    bloom_huge = np.array(bloom_img.filter(ImageFilter.GaussianBlur(radius=60))).astype(np.float32)
    
    # === STEP 6: Horizontal scanlines (DOMINANT) ===
    scanline_mask = np.ones((h, w), dtype=np.float32)
    scan_period = 4
    for y in range(h):
        phase = y % scan_period
        if phase == 0:
            scanline_mask[y, :] = 1.0
        elif phase == 1:
            scanline_mask[y, :] = 0.9
        elif phase == 2:
            scanline_mask[y, :] = 0.15  # dark gap
        else:
            scanline_mask[y, :] = 0.6
    
    # === STEP 7: RGB phosphor columns (secondary to scanlines) ===
    phosphor = np.zeros((h, w, 3), dtype=np.float32)
    for x in range(w):
        col = x % 3
        if col == 0:
            phosphor[:, x, :] = [1.0, 0.2, 0.2]
        elif col == 1:
            phosphor[:, x, :] = [0.2, 1.0, 0.2]
        else:
            phosphor[:, x, :] = [0.2, 0.2, 1.0]
    
    # Apply scanlines + phosphor to base image
    scanned = aberrated.copy()
    for c in range(3):
        scanned[:, :, c] *= scanline_mask
    scanned *= phosphor
    
    # === STEP 8: ADDITIVE BLOOM (the magic) ===
    # Bloom goes ON TOP of the scanlined image
    # This makes bright areas glow THROUGH the scanlines
    final = scanned.copy()
    final += bloom_tight * 0.45   # strong tight glow
    final += bloom_med * 0.30     # medium halo
    final += bloom_wide * 0.15    # soft atmospheric
    final += bloom_huge * 0.08    # very subtle wide haze
    
    # === STEP 9: Vignette ===
    vig = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            d2 = dx**2 + dy**2
            vig[y, x] = max(0, 1.0 - 0.5 * d2)
    
    for c in range(3):
        final[:, :, c] *= vig
    
    # === STEP 10: Glass reflection (diagonal sheen) ===
    sheen = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            t = (x / w * 0.7 + y / h * 0.3)
            sheen[y, x] = math.exp(-(t - 0.25)**2 / 0.008) * 15
            sheen[y, x] += math.exp(-(t - 0.7)**2 / 0.02) * 8  # secondary
    
    for c in range(3):
        final[:, :, c] += sheen
    
    # === STEP 11: Slight noise ===
    noise = np.random.normal(0, 3, final.shape)
    final += noise
    
    # === STEP 12: Final contrast push (deep blacks, hot whites) ===
    final = np.clip(final, 0, 255)
    # Levels adjustment: crush shadows, brighten highlights
    final = np.where(final < 15, final * 0.3, final)  # crush near-blacks
    final = np.where(final > 200, np.minimum(final * 1.1, 255), final)  # push highlights
    
    final = np.clip(final, 0, 255).astype(np.uint8)
    img_out = Image.fromarray(final)
    
    # === STEP 13: Rounded corners (CRT screen) ===
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    corner_r = int(min(w, h) * 0.1)
    md.rounded_rectangle([2, 2, w-3, h-3], radius=corner_r, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=3))
    
    bg = Image.new('RGB', (w, h), (1, 1, 1))
    bg.paste(img_out, mask=mask)
    
    bg.save(output_path)
    print(f"Saved CRT v3: {output_path} ({w}x{h})")

# Large for inspection
apply_crt_v3("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v3_large.png", size=(400, 400))

# Plugin size
apply_crt_v3("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v3.png", size=(175, 175))
