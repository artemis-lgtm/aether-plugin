"""
Generate DALL-E knobs matching Austin's reference:
- Smooth plastic dome knob 
- Single vertical slot/groove as position indicator
- Clean, minimal, slightly domed top
- Matte to slightly satin finish
- Each in a different color
- On transparent/neutral bg for easy extraction
"""
import openai
import requests
import os
import base64
from PIL import Image
from io import BytesIO

API_KEY = open('/Users/artemis/.openclaw/workspace/tools/openai-api-key.txt').read().strip()
client = openai.OpenAI(api_key=API_KEY)

# Colors matching our palette (descriptive names for DALL-E)
KNOB_COLORS = [
    ("soft blue-gray", "swellsens"),
    ("warm tan-brown", "swellattack"),
    ("mint green", "swelldepth"),
    ("dusty pink-magenta", "vinylyear"),
    ("teal-aqua", "vinyldetune"),
    ("light mauve-pink", "psycheshimmer"),
    ("warm cream-gold", "psychespace"),
    ("sky blue", "psychemod"),
    ("seafoam turquoise", "psychewarp"),
    ("sage olive-green", "psychemix"),
    ("coral red", "psychenotches"),
    ("warm orange", "psychesweep"),
    ("lime chartreuse", "lfoshape"),
    ("amber yellow", "lforate"),
    ("periwinkle blue-gray", "lfodepth"),
    ("medium indigo-blue", "lfosyncrate"),
    ("violet purple", "lfophase"),
    ("deep red-crimson", "mastermix"),
    ("muted yellow-olive", "mastergain"),
]

OUT_DIR = "/tmp/aether-art/dalle-knobs"
os.makedirs(OUT_DIR, exist_ok=True)

for color_name, knob_id in KNOB_COLORS:
    out_path = os.path.join(OUT_DIR, f"{knob_id}.png")
    if os.path.exists(out_path):
        print(f"  SKIP {knob_id} (exists)")
        continue
    
    prompt = (
        f"A single {color_name} colored smooth plastic rotary knob, exactly like a washing machine "
        f"or stove dial knob. Smooth rounded dome shape, slightly flat on top. "
        f"Has a single narrow vertical slot/groove cut into the top surface as the position indicator. "
        f"Clean matte plastic finish, not glossy. No text, no markings except the slot. "
        f"The knob is pointing straight up (12 o'clock position). "
        f"Shot from directly above at a slight angle, studio lighting, "
        f"on a solid dark gray (#2A2A2A) background. "
        f"Photorealistic product photography, isolated single object, no shadows visible."
    )
    
    print(f"Generating {knob_id} ({color_name})...")
    try:
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="medium",
        )
        
        # gpt-image-1 returns b64_json by default
        if resp.data[0].b64_json:
            img_data = base64.b64decode(resp.data[0].b64_json)
        else:
            img_data = requests.get(resp.data[0].url).content
        
        img = Image.open(BytesIO(img_data))
        img.save(out_path)
        print(f"  -> {out_path} ({img.size[0]}x{img.size[1]})")
    except Exception as e:
        print(f"  ERROR: {e}")

print("Done generating DALL-E knobs!")
