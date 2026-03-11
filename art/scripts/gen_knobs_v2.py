"""Generate DALL-E knobs matching Austin's reference (smooth dome, single slot groove)."""
import json, base64, urllib.request, os, time

API_KEY = open('/Users/artemis/.openclaw/workspace/tools/openai-api-key.txt').read().strip()
OUT_DIR = "/tmp/aether-art/dalle-knobs"
os.makedirs(OUT_DIR, exist_ok=True)

KNOBS = [
    ("swellsens", "soft blue-gray"),
    ("swellattack", "warm tan-brown"),
    ("swelldepth", "mint green"),
    ("vinylyear", "dusty rose pink"),
    ("vinyldetune", "teal aqua"),
    ("psycheshimmer", "light mauve pink"),
    ("psychespace", "warm cream gold"),
    ("psychemod", "sky blue"),
    ("psychewarp", "seafoam turquoise"),
    ("psychemix", "sage olive green"),
    ("psychenotches", "coral red"),
    ("psychesweep", "warm orange"),
    ("lfoshape", "lime chartreuse green"),
    ("lforate", "amber yellow"),
    ("lfodepth", "periwinkle blue"),
    ("lfosyncrate", "medium indigo blue"),
    ("lfophase", "violet purple"),
    ("mastermix", "deep crimson red"),
    ("mastergain", "muted olive yellow"),
]

for knob_id, color in KNOBS:
    outf = os.path.join(OUT_DIR, f"{knob_id}.png")
    if os.path.exists(outf):
        print(f"SKIP {knob_id}")
        continue

    prompt = (
        f"A single {color} colored smooth plastic rotary knob, exactly like a washing machine "
        f"or stove dial. Smooth rounded dome shape, slightly flat on top. "
        f"Has a single narrow vertical slot groove cut into the top surface as the position "
        f"indicator pointing straight up to 12 oclock. Clean matte plastic finish, not glossy. "
        f"No text, no markings except the slot. Shot from directly above at a slight angle, "
        f"studio lighting, on a solid dark gray background. "
        f"Photorealistic product photography, isolated single object."
    )

    body = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "low",
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )

    print(f"Generating {knob_id} ({color})...", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        
        b64 = data["data"][0].get("b64_json")
        if b64:
            with open(outf, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"  OK -> {outf}", flush=True)
        else:
            url = data["data"][0].get("url", "no url")
            print(f"  Got URL instead: {url[:80]}", flush=True)
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
    
    time.sleep(0.5)

print(f"\nDone! Files in {OUT_DIR}:")
for f in sorted(os.listdir(OUT_DIR)):
    if f.endswith('.png'):
        print(f"  {f}")
