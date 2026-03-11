"""
CRT effect prototype for Austin's portrait.
Goal: Match MSEVEN CRT Tool aesthetic exactly.
Key elements: scanlines, phosphor glow, RGB chromatic aberration,
barrel distortion, color saturation boost, vignette, slight noise.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import math, random

def barrel_distort(img, strength=0.3):
    """Apply barrel distortion (CRT screen curvature)."""
    arr = np.array(img)
    h, w = arr.shape[:2]
    result = np.zeros_like(arr)
    
    cx, cy = w / 2, h / 2
    max_r = math.sqrt(cx**2 + cy**2)
    
    for y in range(h):
        for x in range(w):
            # Normalize coordinates to [-1, 1]
            nx = (x - cx) / cx
            ny = (y - cy) / cy
            
            # Barrel distortion
            r = math.sqrt(nx**2 + ny**2)
            if r > 0:
                nr = r * (1 + strength * r**2)
                theta = math.atan2(ny, nx)
                sx = cx + nr * math.cos(theta) * cx
                sy = cy + nr * math.sin(theta) * cy
                
                si, sj = int(sy), int(sx)
                if 0 <= si < h and 0 <= sj < w:
                    result[y, x] = arr[si, sj]
            else:
                result[y, x] = arr[y, x]
    
    return Image.fromarray(result)

def apply_crt_effect(portrait_path, output_path, size=(175, 175)):
    """Full CRT effect pipeline."""
    
    # Load and resize portrait
    img = Image.open(portrait_path).convert('RGB')
    img = img.resize(size, Image.LANCZOS)
    w, h = img.size
    
    # Step 1: Boost saturation and contrast (CRT phosphors are vivid)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.5)  # 50% more saturated
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)  # 30% more contrast
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)  # slight brightness boost
    
    # Step 2: Barrel distortion (CRT screen curvature)
    # Using a faster numpy approach
    arr = np.array(img).astype(np.float32)
    
    # Create coordinate grids for barrel distortion
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w/2, h/2
    nx = (xx - cx) / cx
    ny = (yy - cy) / cy
    r = np.sqrt(nx**2 + ny**2)
    strength = 0.15  # subtle curvature
    nr = r * (1 + strength * r**2)
    # Map back
    mask = r > 0
    theta = np.where(mask, np.arctan2(ny, nx), 0)
    sx = np.where(mask, cx + nr * np.cos(theta) * cx, xx).astype(int)
    sy = np.where(mask, cy + nr * np.sin(theta) * cy, yy).astype(int)
    sx = np.clip(sx, 0, w-1)
    sy = np.clip(sy, 0, h-1)
    
    distorted = arr[sy, sx]
    
    # Step 3: RGB Chromatic Aberration (shift R and B channels)
    shift = 2  # pixels of shift
    result = np.zeros_like(distorted)
    # Red channel shifted left
    result[:, :, 0] = np.roll(distorted[:, :, 0], -shift, axis=1)
    # Green channel stays
    result[:, :, 1] = distorted[:, :, 1]
    # Blue channel shifted right
    result[:, :, 2] = np.roll(distorted[:, :, 2], shift, axis=1)
    
    # Step 4: Phosphor glow (bloom on bright areas)
    bright = result.copy()
    bright_img = Image.fromarray(bright.astype(np.uint8))
    # Create glow by blurring the bright version
    glow = bright_img.filter(ImageFilter.GaussianBlur(radius=6))
    glow_arr = np.array(glow).astype(np.float32)
    # Screen blend the glow
    result = result.astype(np.float32)
    blended = result + glow_arr * 0.4
    blended = np.clip(blended, 0, 255)
    
    # Step 5: Scanlines
    scanline_period = 3  # every 3 pixels
    for y in range(h):
        if y % scanline_period == 0:
            # Dark scanline
            blended[y, :, :] *= 0.35  # 65% darker
        elif y % scanline_period == 1:
            blended[y, :, :] *= 0.85  # slightly dimmer between
    
    # Step 6: Phosphor sub-pixel pattern (RGB stripes like real CRT)
    for x in range(w):
        channel = x % 3
        for c in range(3):
            if c != channel:
                blended[:, x, c] *= 0.7  # dim non-primary channels
    
    # Step 7: Vignette (darker edges, like curved CRT glass)
    vig = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            d = math.sqrt(dx**2 + dy**2)
            vig[y, x] = max(0, 1 - d * 0.6)  # darken toward edges
    
    for c in range(3):
        blended[:, :, c] *= vig
    
    # Step 8: Slight noise/static
    noise = np.random.normal(0, 8, blended.shape)
    blended += noise
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    
    img_out = Image.fromarray(blended)
    
    # Step 9: Rounded corners (CRT screen shape)
    # Create mask with rounded corners
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    corner_r = 12
    md.rounded_rectangle([0, 0, w-1, h-1], radius=corner_r, fill=255)
    
    # Black background
    final = Image.new('RGB', (w, h), (5, 5, 5))
    final.paste(img_out, mask=mask)
    
    # Step 10: CRT bezel/frame glow
    # Add a subtle colored edge glow
    frame = Image.new('RGBA', (w+20, h+20), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    # Outer glow
    fd.rounded_rectangle([2, 2, w+18, h+18], radius=corner_r+4, 
                         outline=(40, 80, 60, 100), width=3)
    fd.rounded_rectangle([5, 5, w+15, h+15], radius=corner_r+2,
                         outline=(20, 40, 30, 60), width=2)
    
    # Composite
    result_frame = Image.new('RGB', (w+20, h+20), (5, 5, 5))
    result_frame.paste(final, (10, 10))
    result_rgba = result_frame.convert('RGBA')
    result_rgba = Image.alpha_composite(result_rgba, frame)
    
    result_rgba.convert('RGB').save(output_path)
    print(f"Saved CRT effect: {output_path} ({w+20}x{h+20})")
    return output_path

# Generate
portrait = "/tmp/aether-art/austin-portrait-square.jpg"
output = "/tmp/aether-art/crt_portrait_v1.png"
apply_crt_effect(portrait, output, size=(175, 175))

# Also save a larger version for easier visual inspection
apply_crt_effect(portrait, "/tmp/aether-art/crt_portrait_v1_large.png", size=(400, 400))
