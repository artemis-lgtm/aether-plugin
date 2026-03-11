"""
CRT v6 -- the bloom must come from WITHIN the tube.
Key: bloom is pre-grid, fills scanline gaps from behind.
Grid dissolves aggressively. Bloom carries color. 
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import math

def apply_crt_v6(portrait_path, output_path, size=(400, 400)):
    img = Image.open(portrait_path).convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    w, h = img.size
    cx, cy = w/2.0, h/2.0
    
    # === Warm phosphor color grading ===
    img = ImageEnhance.Color(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.7)
    img = ImageEnhance.Brightness(img).enhance(1.2)
    
    arr = np.array(img).astype(np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.15, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.0, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.7, 0, 255)
    
    # Pre-blur
    soft = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    soft = soft.filter(ImageFilter.GaussianBlur(radius=1.2))
    arr = np.array(soft).astype(np.float32)
    
    # === Barrel distortion ===
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - cx) / cx
    ny = (yy - cy) / cy
    r2 = nx**2 + ny**2
    factor = 1 + 0.20 * r2
    sx = (cx + nx * factor * cx).astype(int)
    sy = (cy + ny * factor * cy).astype(int)
    valid = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    distorted = np.zeros_like(arr)
    distorted[valid] = arr[sy[valid], sx[valid]]
    
    # === Chromatic aberration (STRONGER, more visible) ===
    shift_r = 3
    shift_b = 3
    aberrated = np.zeros_like(distorted)
    # Red: shift right and slightly down
    aberrated[1:, shift_r:, 0] = distorted[:-1, :-shift_r, 0]
    # Green: center
    aberrated[:, :, 1] = distorted[:, :, 1]
    # Blue: shift left and slightly up
    aberrated[:-1, :-shift_b, 2] = distorted[1:, shift_b:, 2]
    
    # === Luminance map ===
    luminance = aberrated.max(axis=2)
    lum_norm = np.clip(luminance / 255.0, 0, 1)
    
    # ====== THE CORE: PHOSPHOR EMISSION MODEL ======
    
    # LAYER 1: Phosphor grid image (the actual pixel structure)
    # Scanlines
    scan_period = 5
    scanline = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        phase = y % scan_period
        if phase in [0, 1]:
            scanline[y, :] = 1.0
        elif phase == 2:
            scanline[y, :] = 0.05  # nearly black gap
        elif phase == 3:
            scanline[y, :] = 0.3
        else:
            scanline[y, :] = 0.85
    
    # Aperture grille (vertical RGB stripes -- MSEVEN style)
    grille = np.ones((h, w, 3), dtype=np.float32)
    for x in range(w):
        col = x % 3
        if col == 0:
            grille[:, x, :] = [1.0, 0.15, 0.15]
        elif col == 1:
            grille[:, x, :] = [0.15, 1.0, 0.15]
        else:
            grille[:, x, :] = [0.15, 0.15, 1.0]
    
    # ADAPTIVE: grid dissolves in bright areas (AGGRESSIVE)
    dissolve = np.clip(lum_norm * 2.0, 0, 1)  # full dissolve above 50% brightness
    for c in range(3):
        grille[:, :, c] = grille[:, :, c] * (1 - dissolve) + 1.0 * dissolve
    adaptive_scan = scanline * (1 - dissolve * 0.8) + dissolve * 0.8
    
    # Apply grid
    gridded = aberrated.copy()
    for c in range(3):
        gridded[:, :, c] *= adaptive_scan
    gridded *= grille
    
    # LAYER 2: Phosphor bloom (from pre-grid image, COLORED)
    # This is the light that bleeds BETWEEN phosphor gaps
    bloom_src = Image.fromarray(np.clip(aberrated, 0, 255).astype(np.uint8))
    
    # Multi-scale bloom (COLORED, not desaturated)
    b1 = np.array(bloom_src.filter(ImageFilter.GaussianBlur(radius=3))).astype(np.float32)
    b2 = np.array(bloom_src.filter(ImageFilter.GaussianBlur(radius=8))).astype(np.float32)
    b3 = np.array(bloom_src.filter(ImageFilter.GaussianBlur(radius=18))).astype(np.float32)
    b4 = np.array(bloom_src.filter(ImageFilter.GaussianBlur(radius=35))).astype(np.float32)
    
    # Partially desaturate (highlights go toward warm white, mids keep color)
    for b in [b1, b2, b3, b4]:
        lum_b = b.mean(axis=2, keepdims=True)
        brightness = lum_b / 255.0
        # More desaturation in brighter areas (highlights -> white-hot)
        desat = np.clip(brightness * 1.5, 0, 0.7)
        b[:] = b * (1 - desat) + lum_b * desat
        # Warm tint the bloom
        b[:, :, 0] *= 1.08  # warm red
        b[:, :, 2] *= 0.92  # reduce blue
    
    # Combine: tight bloom strong, wide bloom atmospheric
    bloom = b1 * 0.55 + b2 * 0.40 + b3 * 0.22 + b4 * 0.12
    
    # LAYER 3: Composite -- grid + bloom filling gaps
    # The bloom fills in the scanline gaps (light bleeding through)
    final = gridded + bloom
    
    # === Vignette (strong corner falloff) ===
    vig = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            d2 = dx**2 + dy**2
            vig[y, x] = max(0, 1.0 - 0.75 * d2)
    for c in range(3):
        final[:, :, c] *= vig
    
    # === Glass reflection (BOLDER curved arc) ===
    sheen = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            nx2 = (x - cx) / cx
            ny2 = (y - cy) / cy
            # Main reflection: curved arc across upper-left
            arc = nx2 * 0.4 + ny2 * 0.6 + 0.35
            sheen[y, x] = math.exp(-arc**2 / 0.015) * 22
            # Broad secondary
            arc2 = -nx2 * 0.3 - ny2 * 0.7 + 0.3
            sheen[y, x] += math.exp(-arc2**2 / 0.04) * 8
    for c in range(3):
        final[:, :, c] += sheen
    
    # === Camera grain (heavier in shadows) ===
    base_noise = np.random.normal(0, 3.5, final.shape)
    dark_mult = np.clip(1.5 - lum_norm, 0.5, 2.0)
    for c in range(3):
        final[:, :, c] += base_noise[:, :, c] * dark_mult
    
    # === S-curve + shadow crush ===
    final = np.clip(final, 0, 300) / 300.0  # allow bloom to push above 255 before curve
    # S-curve
    final = final ** 0.88  # slight gamma lift for midtones
    final = np.where(final < 0.06, final * 0.15, final)  # hard shadow crush
    final = np.clip(final * 255, 0, 255).astype(np.uint8)
    
    img_out = Image.fromarray(final)
    
    # === Bezel ===
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    corner_r = int(min(w, h) * 0.12)
    inset = 10
    md.rounded_rectangle([inset, inset, w-inset-1, h-inset-1], radius=corner_r, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
    
    bg = Image.new('RGB', (w, h), (2, 2, 2))
    bgd = ImageDraw.Draw(bg)
    bgd.rounded_rectangle([inset-3, inset-3, w-inset+2, h-inset+2],
                          radius=corner_r+3, outline=(22, 22, 20), width=2)
    bg.paste(img_out, mask=mask)
    
    bg.save(output_path)
    print(f"Saved CRT v6: {output_path} ({w}x{h})")

apply_crt_v6("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v6_large.png", size=(400, 400))
apply_crt_v6("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v6.png", size=(175, 175))
