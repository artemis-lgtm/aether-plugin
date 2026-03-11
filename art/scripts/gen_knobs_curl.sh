#!/bin/bash
# Generate DALL-E knobs one at a time using curl
API_KEY=$(cat /Users/artemis/.openclaw/workspace/tools/openai-api-key.txt)
OUT_DIR="/tmp/aether-art/dalle-knobs"
mkdir -p "$OUT_DIR"

declare -A KNOBS
KNOBS["swellsens"]="soft blue-gray"
KNOBS["swellattack"]="warm tan-brown"
KNOBS["swelldepth"]="mint green"
KNOBS["vinylyear"]="dusty rose pink"
KNOBS["vinyldetune"]="teal aqua"
KNOBS["psycheshimmer"]="light mauve pink"
KNOBS["psychespace"]="warm cream gold"
KNOBS["psychemod"]="sky blue"
KNOBS["psychewarp"]="seafoam turquoise"
KNOBS["psychemix"]="sage olive green"
KNOBS["psychenotches"]="coral red"
KNOBS["psychesweep"]="warm orange"
KNOBS["lfoshape"]="lime chartreuse green"
KNOBS["lforate"]="amber yellow"
KNOBS["lfodepth"]="periwinkle blue"
KNOBS["lfosyncrate"]="medium indigo blue"
KNOBS["lfophase"]="violet purple"
KNOBS["mastermix"]="deep crimson red"
KNOBS["mastergain"]="muted olive yellow"

for knob_id in "${!KNOBS[@]}"; do
    color="${KNOBS[$knob_id]}"
    outf="$OUT_DIR/${knob_id}.png"
    
    if [ -f "$outf" ]; then
        echo "SKIP $knob_id"
        continue
    fi
    
    echo "Generating $knob_id ($color)..."
    
    PROMPT="A single ${color} colored smooth plastic rotary knob, exactly like a washing machine or stove dial. Smooth rounded dome shape, slightly flat on top. Has a single narrow vertical slot groove cut into the top as the position indicator pointing to 12 oclock. Clean matte plastic finish, not glossy or shiny. No text, no markings except the slot. Shot from directly above at slight angle, studio lighting, on a solid dark gray background. Photorealistic product photography, isolated single object."
    
    curl -s https://api.openai.com/v1/images/generations \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      -d "$(python3 -c "import json; print(json.dumps({'model':'gpt-image-1','prompt':'''$PROMPT''','n':1,'size':'1024x1024','quality':'low'}))")" | \
    python3 -c "
import json, sys, base64
r = json.load(sys.stdin)
if 'data' in r and 'b64_json' in r['data'][0]:
    with open('$outf','wb') as f:
        f.write(base64.b64decode(r['data'][0]['b64_json']))
    print('  OK -> $outf')
else:
    print('  ERROR:', json.dumps(r)[:200])
"
done

echo "ALL DONE"
ls -la "$OUT_DIR"/*.png | wc -l
