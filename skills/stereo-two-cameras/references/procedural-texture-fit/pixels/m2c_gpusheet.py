#!/usr/bin/env python3
"""The browser's drawings beside the native ones (milestone 2c): per texture, at 1:1 around the corner of four tiles,
the native drawing, WebGPU's whole, WebGPU's sixteen tiles put together, the WebAssembly module in the browser, and the
difference of WebGPU against native multiplied by 32 (black: the same); then the timings table from the result files.

m2c_gpusheet.py NATIVEDIR EVIDENCE RUN... (each RUN is OUTDIR:TAG; the first holds the WebAssembly drawings)"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

nat, ev = sys.argv[1:3]
runs = [r.split(':') for r in sys.argv[3:]]
try:
    FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
except OSError:
    FONT = ImageFont.load_default()
out0, tag0 = runs[0]
res0 = json.load(open('%s/%s-result.json' % (out0, tag0)))
names = sorted(res0['textures'])
T = 256
box = (768, 768, 1280, 1280)
sh = Image.new('RGB', (10 + 5 * (T + 8), len(names) * (T + 34) + 40), 'white')
d = ImageDraw.Draw(sh)
d.text((10, 8), 'At 1:1 around the corner of four tiles: native | WebGPU whole | WebGPU 16 tiles put together | WebAssembly in the browser | |WebGPU - native| x 32 (adapter: %s %s)' % (res0['adapter']['vendor'], res0['adapter']['architecture']), fill='black', font=FONT)
for r, n in enumerate(names):
    y = 36 + r * (T + 34)
    d.text((10, y), n, fill='black', font=FONT)
    a = Image.open('%s/%s.ppm' % (nat, n)).convert('RGB')
    ims = [a]
    for k in ('webgpu', 'webgpu-tiles', 'wasm'):
        p = '%s/%s-%s-%s.png' % (out0, tag0, n, k)
        ims.append(Image.open(p).convert('RGB') if os.path.exists(p) else Image.new('RGB', a.size, 'grey'))
    da = np.abs(np.asarray(a).astype(int) - np.asarray(ims[1]).astype(int))
    ims.append(Image.fromarray(np.clip(da * 32, 0, 255).astype(np.uint8)))
    for k, im in enumerate(ims):
        sh.paste(im.crop(box).resize((T, T), Image.LANCZOS), (10 + k * (T + 8), y + 16))
sh.save(ev + '/webgpu-beside-native.jpg', quality=90)

with open(ev + '/timings.md', 'w') as f:
    f.write('# Drawing times in the browser (milestone 2c)\n\n')
    f.write('Debian chromium 156 in a container, WebGPU on Vulkan. A whole is one submission of every operator of the procedure at 2048 by 2048 (with its margin), timed from the submission to the GPU saying it is done, the median of the timed runs after one warm-up; the tiles are the sixteen 512 pixel tiles each drawn through its own window, one submission each, summed. The WebAssembly module ran in the same page on one processor thread.\n\n')
    for out, tag in runs:
        r = json.load(open('%s/%s-result.json' % (out, tag)))
        f.write('## %s: %s %s\n\n' % (tag, r['adapter']['vendor'], r['adapter']['architecture']))
        f.write('| texture | operators | WebGPU whole (ms) | WebGPU 16 tiles (ms) | WebAssembly whole (ms) | WebAssembly 16 tiles (ms) |\n|---|---|---|---|---|---|\n')
        for n in sorted(r['textures']):
            t = r['textures'][n]
            med = lambda v: sorted(v)[len(v) // 2]
            f.write('| %s | %d | %.1f | %.1f | %s | %s |\n' % (n, t['operators'], med(t['gpu_whole_ms']), med(t['gpu_tiles_ms']),
                    '%.0f' % t['wasm_whole_ms'] if 'wasm_whole_ms' in t else '-', '%.0f' % t['wasm_tiles_ms'] if 'wasm_tiles_ms' in t else '-'))
        f.write('\n')
print('written', ev + '/webgpu-beside-native.jpg', ev + '/timings.md')
