"""
CRT effect v4 -- fixing the soul.
- Less saturation, more phosphor-accurate warmth
- Bloom desaturates toward white at peaks
- Blacker blacks (bloom doesn't lift shadows)
- Photographed-screen feel (glass haze, reflection)
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import math

def apply_crt_v4(portrait_path, output_path, size=(400, 400)):
    img = Image.open(portrait_path).convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    w, h = img.size
    cx, cy = w/2.0, h/2.0
    
    # === Color grading: RESTRAINED, warm phosphor palette ===
    img = ImageEnhance.Color(img).enhance(1.4)       # moderate saturation
    img = ImageEnhance.Contrast(img).enhance(1.5)     # high contrast
    img = ImageEnhance.Brightness(img).enhance(1.1)
    
    arr = np.array(img).astype(np.float32)
    
    # Warm amber phosphor shift (NOT rainbow)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.12, 0, 255)  # warm red
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.02, 0, 255)  # neutral green
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.82, 0, 255)  # reduced blue
    
    # === Pre-blur (electron beam softness) ===
    soft = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    soft = soft.filter(ImageFilter.GaussianBlur(radius=1.2))
    arr = np.array(soft).astype(np.float32)
    
    # === Barrel distortion (stronger) ===
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - cx) / cx
    ny = (yy - cy) / cy
    r2 = nx**2 + ny**2
    factor = 1 + 0.22 * r2  # stronger curvature
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
    
    # === Create bloom BEFORE scanlines ===
    bloom_src = np.clip(aberrated, 0, 255).astype(np.uint8)
    bloom_img = Image.fromarray(bloom_src)
    
    # Threshold: only bloom from bright areas (>120)
    bright_mask = (aberrated.max(axis=2) > 120).astype(np.float32)
    bright_only = aberrated * bright_mask[:, :, np.newaxis]
    bright_img = Image.fromarray(np.clip(bright_only, 0, 255).astype(np.uint8))
    
    # Multi-scale bloom from bright areas only
    b_tight = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=5))).astype(np.float32)
    b_med = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=15))).astype(np.float32)
    b_wide = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=35))).astype(np.float32)
    b_huge = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=55))).astype(np.float32)
    
    # Desaturate bloom toward white (key: bloom should be white-hot at peaks)
    for b in [b_tight, b_med, b_wide, b_huge]:
        lum = b.mean(axis=2, keepdims=True)
        # Blend toward luminance (desaturate)
        b[:] = b * 0.4 + lum * 0.6  # 60% desaturated bloom = white-hot
    
    # Also full image bloom (softer, lower intensity)
    full_bloom = np.array(bloom_img.filter(ImageFilter.GaussianBlur(radius=25))).astype(np.float32)
    full_lum = full_bloom.mean(axis=2, keepdims=True)
    full_bloom = full_bloom * 0.3 + full_lum * 0.7
    
    # === Scanlines (coarser, bolder) ===
    scan_period = 5  # coarser than before
    scanline_mask = np.ones((h, w), dtype=np.float32)
    for y in range(h):
        phase = y % scan_period
        if phase == 0:
            scanline_mask[y, :] = 1.0
        elif phase == 1:
            scanline_mask[y, :] = 0.85
        elif phase == 2:
            scanline_mask[y, :] = 0.1   # very dark gap
        elif phase == 3:
            scanline_mask[y, :] = 0.5
        else:
            scanline_mask[y, :] = 0.9
    
    # RGB phosphor columns (subtle)
    phosphor = np.ones((h, w, 3), dtype=np.float32)
    for x in range(w):
        col = x % 3
        if col == 0:
            phosphor[:, x, :] = [1.0, 0.25, 0.25]
        elif col == 1:
            phosphor[:, x, :] = [0.25, 1.0, 0.25]
        else:
            phosphor[:, x, :] = [0.25, 0.25, 1.0]
    
    # Apply scanlines + phosphor
    scanned = aberrated.copy()
    for c in range(3):
        scanned[:, :, c] *= scanline_mask
    scanned *= phosphor
    
    # === ADDITIVE BLOOM on top of scanlines ===
    final = scanned.copy()
    final += b_tight * 0.50
    final += b_med * 0.35
    final += b_wide * 0.18
    final += b_huge * 0.10
    final += full_bloom * 0.06  # subtle overall atmosphere
    
    # === Vignette (stronger -- dark edges) ===
    vig = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            d2 = dx**2 + dy**2
            vig[y, x] = max(0, 1.0 - 0.65 * d2)  # stronger falloff
    
    for c in range(3):
        final[:, :, c] *= vig
    
    # === Glass haze (photographed-screen feel) ===
    # Very subtle uniform haze (simulates light scattering in glass)
    avg_brightness = final.mean() * 0.015
    final += avg_brightness
    
    # === Glass reflection (diagonal sheen, subtle) ===
    sheen = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            t = x / w * 0.6 + y / h * 0.4
            sheen[y, x] = math.exp(-(t - 0.22)**2 / 0.005) * 12
    for c in range(3):
        final[:, :, c] += sheen
    
    # === Noise ===
    noise = np.random.normal(0, 2.5, final.shape)
    final += noise
    
    # === CRUSH BLACKS (bloom must not lift shadows) ===
    # Apply a tone curve that keeps darks dark
    final = np.clip(final, 0, 255)
    # Gamma curve that preserves blacks
    normalized = final / 255.0
    # S-curve: darken shadows, brighten highlights
    curved = normalized ** 0.9  # slight gamma
    # Additional shadow crush
    shadow_mask = (normalized < 0.15).astype(np.float32)
    curved *= (1 - shadow_mask * 0.5)  # darken shadows more
    final = (curved * 255).astype(np.float32)
    
    final = np.clip(final, 0, 255).astype(np.uint8)
    img_out = Image.fromarray(final)
    
    # === Rounded corners with dark bezel ===
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    corner_r = int(min(w, h) * 0.12)
    # Inset the screen area (visible bezel border)
    inset = 8
    md.rounded_rectangle([inset, inset, w-inset-1, h-inset-1], radius=corner_r, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Dark bezel background
    bg = Image.new('RGB', (w, h), (3, 3, 3))
    # Subtle bezel highlight
    bgd = ImageDraw.Draw(bg)
    bgd.rounded_rectangle([inset-2, inset-2, w-inset+1, h-inset+1], 
                          radius=corner_r+2, outline=(30, 30, 28), width=2)
    
    bg.paste(img_out, mask=mask)
    
    bg.save(output_path)
    print(f"Saved CRT v4: {output_path} ({w}x{h})")

apply_crt_v4("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v4_large.png", size=(400, 400))
apply_crt_v4("/tmp/aether-art/austin-portrait-square.jpg",
             "/tmp/aether-art/crt_portrait_v4.png", size=(175, 175))
