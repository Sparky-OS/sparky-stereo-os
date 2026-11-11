#!/usr/bin/env python3
"""Copy the milestone 3 runs' screenshots into the evidence folder as JPEG (quality 85, full size) and their records
as small JSON: m3_evidence.py RUNS-DIR EVIDENCE-DIR. The submission logs stay in the scratch folder (large)."""
import glob, json, os, sys
from PIL import Image
runs, ev = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(ev, 'screens'), exist_ok=True)
os.makedirs(os.path.join(ev, 'records'), exist_ok=True)
n = 0
for png in sorted(glob.glob(os.path.join(runs, '*', '*.png'))):
    tag = os.path.basename(os.path.dirname(png))
    base = os.path.basename(png)
    if not base.startswith(tag + '-') or base[len(tag) + 1:][:1] not in '12345':
        continue
    Image.open(png).convert('RGB').save(os.path.join(ev, 'screens', base[:-4] + '.jpg'), quality=85)
    n += 1
for rp in sorted(glob.glob(os.path.join(runs, '*', '*-result.json'))):
    r = json.load(open(rp))
    r.pop('submissionLog', None)
    r['rateSamples'] = len(r.pop('rate', []))
    json.dump(r, open(os.path.join(ev, 'records', os.path.basename(rp)), 'w'), indent=1)
print('%d screenshots, %d records' % (n, len(glob.glob(os.path.join(ev, 'records', '*.json')))))
