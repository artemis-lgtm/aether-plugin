"""
CRT v5 -- tighter hotter bloom, warmer palette, glass reflection.
Key insight: bloom should OVERRIDE phosphor grid in bright areas.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import math

def apply_crt_v5(portrait_path, output_path, size=(400, 400)):
    img = Image.open(portrait_path).convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    w, h = img.size
    cx, cy = w/2.0, h/2.0
    
    # === Color: WARM, amber phosphor palette ===
    img = ImageEnhance.Color(img).enhance(1.3)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = ImageEnhance.Brightness(img).enhance(1.15)
    
    arr = np.array(img).astype(np.float32)
    
    # Strong warm shift
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.18, 0, 255)  # warm red
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.0, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.72, 0, 255)  # crush blue hard
    
    # Pre-blur
    soft = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    soft = soft.filter(ImageFilter.GaussianBlur(radius=1.0))
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
    
    # === Chromatic aberration ===
    shift = 2
    aberrated = np.zeros_like(distorted)
    aberrated[:, shift:, 0] = distorted[:, :-shift, 0]
    aberrated[:, :, 1] = distorted[:, :, 1]
    aberrated[:, :-shift, 2] = distorted[:, shift:, 2]
    
    # === Compute brightness map for adaptive effects ===
    luminance = aberrated.max(axis=2)  # per-pixel brightness
    lum_norm = luminance / 255.0       # 0-1
    
    # === Bloom (TIGHT HOT CORE + rapid falloff) ===
    # Only bloom from bright pixels
    bright_thresh = 100
    bright_mask = (luminance > bright_thresh).astype(np.float32)
    bright_only = aberrated * bright_mask[:, :, np.newaxis]
    bright_img = Image.fromarray(np.clip(bright_only, 0, 255).astype(np.uint8))
    
    # Tight bloom (small radius, high intensity)
    b1 = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=3))).astype(np.float32)
    b2 = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=8))).astype(np.float32)
    b3 = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=20))).astype(np.float32)
    b4 = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=40))).astype(np.float32)
    
    # Desaturate bloom heavily toward white-hot
    for b in [b1, b2, b3, b4]:
        lum_b = b.mean(axis=2, keepdims=True)
        b[:] = b * 0.25 + lum_b * 0.75  # 75% desaturated = near white
    
    # Combine bloom layers (tight = strong, wide = subtle)
    bloom_combined = b1 * 0.60 + b2 * 0.40 + b3 * 0.20 + b4 * 0.10
    
    # === Scanlines (adaptive: FADE in bright areas) ===
    scan_period = 5
    scanline_mask = np.ones((h, w), dtype=np.float32)
    for y in range(h):
        phase = y % scan_period
        if phase == 0:
            scanline_mask[y, :] = 1.0
        elif phase == 1:
            scanline_mask[y, :] = 0.85
        elif phase == 2:
            scanline_mask[y, :] = 0.08  # very dark gap
        elif phase == 3:
            scanline_mask[y, :] = 0.45
        else:
            scanline_mask[y, :] = 0.92
    
    # Adaptive: scanlines less visible in bright areas (phosphor blowout)
    # When pixel is bright, scanline gap fills in
    adaptive_scan = scanline_mask[:, :] + lum_norm * 0.4
    adaptive_scan = np.clip(adaptive_scan, 0, 1)
    
    # RGB phosphor columns (also adaptive)
    phosphor = np.ones((h, w, 3), dtype=np.float32)
    for x in range(w):
        col = x % 3
        if col == 0:
            phosphor[:, x, :] = [1.0, 0.2, 0.2]
        elif col == 1:
            phosphor[:, x, :] = [0.2, 1.0, 0.2]
        else:
            phosphor[:, x, :] = [0.2, 0.2, 1.0]
    
    # In bright areas, phosphor grid fades (all channels approach 1.0)
    for c in range(3):
        phosphor[:, :, c] = phosphor[:, :, c] + lum_norm * (1.0 - phosphor[:, :, c]) * 0.6
    
    # Apply
    scanned = aberrated.copy()
    for c in range(3):
        scanned[:, :, c] *= adaptive_scan
    scanned *= phosphor
    
    # === Add bloom ADDITIVELY ===
    final = scanned + bloom_combined
    
    # === Vignette (electron beam falloff) ===
    vig = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            d2 = dx**2 + dy**2
            vig[y, x] = max(0, 1.0 - 0.7 * d2)
    for c in range(3):
        final[:, :, c] *= vig
    
    # === Glass reflection (curved specular) ===
    sheen = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            # Curved glass reflection (top-left to center arc)
            nx2 = (x - cx) / cx
            ny2 = (y - cy) / cy
            # Reflection curve
            t = nx2 * 0.5 + ny2 * 0.5 + 0.3
            sheen[y, x] = math.exp(-(t)**2 / 0.03) * 18
            # Secondary reflection (bottom right)
            t2 = nx2 * 0.4 - ny2 * 0.6 - 0.2
            sheen[y, x] += math.exp(-(t2)**2 / 0.05) * 6
    for c in range(3):
        final[:, :, c] += sheen
    
    # === Camera noise/grain (photographed screen) ===
    noise = np.random.normal(0, 4, final.shape)  # moderate grain
    # More noise in dark areas (camera sensor behavior)
    dark_boost = (1.0 - lum_norm) * 3
    for c in range(3):
        final[:, :, c] += noise[:, :, c] * (1 + dark_boost)
    
    # === Tone curve: S-curve with shadow crush ===
    final = np.clip(final, 0, 255) / 255.0
    # S-curve
    final = 0.5 * (1 + np.sign(final - 0.5) * np.abs(2 * final - 1) ** 0.85)
    # Extra shadow crush
    final = np.where(final < 0.08, final * 0.3, final)
    final = (final * 255).astype(np.float32)
    
    final = np.clip(final, 0, 255).astype(np.uint8)
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
                          radius=corner_r+3, outline=(25, 25, 23), width=2)
    bgd.rounded_rectangle([inset-1, inset-1, w-inset, h-inset],
                          radius=corner_r+1, outline=(15, 15, 13), width=1)
    bg.paste(img_out, mask=mask)
    
    bg.save(output_path)
    print(f"Saved CRT v5: {output_path} ({w}x{h})")

apply_crt_v5("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v5_large.png", size=(400, 400))
apply_crt_v5("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v5.png", size=(175, 175))
