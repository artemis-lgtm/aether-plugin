# Aether / Austin's Secret Sauce — Art Pipeline

## Overview
All visual assets for the plugin are generated programmatically. No Photoshop.
The pipeline: DALL-E generation → PIL/numpy compositing → Blender knob rendering → JUCE BinaryData embedding.

## Directory Structure
```
art/
├── scripts/          # All Python/shell scripts (85 files, full iteration history)
├── assets/           # Final shipped assets only
├── knob-frames/      # 128-frame filmstrips per section (5 color variants)
├── reference/        # Key DALL-E generations, HDR environments
└── README.md         # This file
```

## The Face (Background Image)
**Final script:** `assets/make_face_shipped.py` (make-face-v15.py)
**Output:** 1020x620 PNG → embedded as JUCE BinaryData `background_png`

### What it does:
1. Loads a DALL-E-generated wood/duct-tape pedal face
2. Composites CRT portrait into bottom-right corner (position: px=810, py=405, pw=175, ph=175)
3. Draws inset bevel around portrait (10px shadow, 6px highlight)
4. Draws red neon border with glow (2px frame at bx0=808, by0=403, bx1=987, by1=582)
5. Draws duct tape section labels with "sharpie" handwritten font
6. Draws knob labels in gray below each knob position
7. Animated neon flicker is done in JUCE (PluginEditor.cpp), not in the static image

### Key learnings (hard-won):
- **Bevel shadows:** Use multiplicative darkening (`factor = 1.0 - (0.85 * s ** 0.5)`) to preserve wood grain texture
- **Bevel highlights:** Use additive RGBA overlay on dark wood (multiplicative brighten is invisible on dark surfaces)
- **Diagonal corner fill:** Top-left corner where shadow bands meet needs explicit fill: `for i in range(bevel_w): for j in range(bevel_w - i):`
- **CRT effect is 80% bloom.** Light must EMIT, not filter. Multiple blur radii for glow layers.
- **Vision model QA at 3x zoom is harsher than human perception at 1x.** Don't over-optimize for zoom.

### sharpie_bold() function:
```python
# thin=True: single stroke, alpha 180
# medium=True: cardinal offsets only (4 draws α150 + center α255) — used for knob labels
# default: full 3x3 grid (9 draws α180 + center α255) — used for section titles
```

## CRT Portrait Effect
**Final script:** `assets/crt_effect_shipped.py` (crt_effect_v10.py)
**Input:** `assets/austin-portrait-square.jpg`
**Output:** 175x175 CRT portrait with phosphor glow, scanlines, bloom, vignette

### Iteration history (10 versions):
- v1-v3: Basic scanlines + color shift. Too dark.
- v4-v5: Added bloom. Getting warmer.
- v6-v7: Added vignette + phosphor dot pattern. Better but flat.
- v8: Breakthrough — multi-radius bloom (the "80% bloom" insight). Rated 9/10. Shipped in v4.18.
- v9: Brightness pulled back to 0.9. Too dim.
- v10: Brightness 1.0 (sweet spot). Bloom weights halved from v8 but still present. Shipped in v4.19+.

### Key parameters:
- Bloom weights: halved from v8 aggressive values
- Glass reflection: subtle, halved from v8
- Brightness multiplier: 1.0
- Scanline gap: tuned for 175px display size

## Knob Filmstrips
**Script:** `scripts/render_knob_filmstrips.py` (Blender Python)
**Output:** 128 frames per section, assembled into vertical filmstrip PNGs

### Color variants (per section):
- **Swell:** warm orange-red dome
- **Vinyl:** olive/green dome  
- **Psyche:** purple/violet dome
- **LFO:** blue dome
- **Master:** silver/chrome dome

### Pipeline:
1. `render_knob_filmstrips.py` renders 128 rotation angles in Blender
2. `assemble_filmstrips.py` concatenates frames into vertical strip
3. Strips embedded as JUCE BinaryData (knob_swell_png, etc.)
4. `FilmstripLookAndFeel` in PluginEditor.cpp reads strip, divides by frame count

### Matte dome knobs (final direction):
- Rejected: DALL-E knobs (uncanny), hex faceted (too busy), chrome (too shiny)
- Approved: Matte colored domes with subtle specular. Pretty Princess pedal reference.
- Script for final matte: `scripts/make_knobs_v6_matte.py`

## DALL-E Prompting
Face images were generated via OpenAI DALL-E (gpt-image-1 / dall-e-3).

### What worked:
- "guitar effects pedal face, dark walnut wood panel, gray duct tape strips with black marker labels"
- Specifying exact layout (two columns, tape positions) in the prompt
- Generating at high res then downscaling to 1020x620

### What didn't work:
- Trying to get DALL-E to render knobs (always wrong perspective/count)
- Trying to get text rendered correctly (composited programmatically instead)
- Chrome/metal plate attempts (looked fake)

## Neon Flicker Animation (JUCE side)
Not in the art pipeline but important context:
- 30fps timer in PluginEditor.cpp
- Breathing: `0.7 + 0.3 * sin(phase)` base brightness
- Random stutter: 5% chance of dim frame, 2% chance of bright flash
- Applied to title text glow AND portrait border glow simultaneously
- Red neon only (Austin's rule: not pink)

## Design Rules (Austin's preferences)
- RED neon, never pink
- Dark walnut wood skin, never teal
- Gray duct tape, never masking tape
- Two-column layout
- Psyche 7 knobs in one row
- Matte dome knobs
- No emojis anywhere
- "Austin's Secret Sauce" on duct tape (hand-drawn marker style)
- Portrait is "perfect" — do NOT modify
