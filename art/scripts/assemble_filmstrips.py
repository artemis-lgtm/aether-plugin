"""Assemble individual frames into horizontal filmstrip PNGs."""
from PIL import Image
import os

FRAME_SIZE = 128
NUM_FRAMES = 128
SECTIONS = ['swell', 'vinyl', 'master', 'psyche', 'lfo']

for section in SECTIONS:
    frame_dir = f'/tmp/aether-art/knob-frames-{section}'
    strip = Image.new('RGBA', (FRAME_SIZE * NUM_FRAMES, FRAME_SIZE), (0, 0, 0, 0))
    
    for i in range(NUM_FRAMES):
        frame_path = f'{frame_dir}/frame_{i:03d}.png'
        if os.path.exists(frame_path):
            frame = Image.open(frame_path).convert('RGBA')
            strip.paste(frame, (i * FRAME_SIZE, 0))
    
    out = f'/tmp/aether-plugin/resources/knob-{section}.png'
    strip.save(out)
    print(f'{section}: {strip.size} -> {out}')

# Also make the HD version (already 128px, so same as regular)
# And a combined default strip for fallback
print("Done!")
