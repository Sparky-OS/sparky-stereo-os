#!/usr/bin/env python3
"""Red and green tests of mixedtex.py validate (ORDER 508, milestone 3): the courtyard as built must pass; each broken
copy (one rule broken at a time) must fail with the sentence that names the rule; the writer's per-eye form must
pass. m3_validator_tests.py SCENE-DIR WORKDIR (WORKDIR: a new folder; copies of the scene are made there)."""
import copy, json, os, shutil, subprocess, sys

scene, work = sys.argv[1], sys.argv[2]
tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'tester', 'mixedtex.py')
os.makedirs(work, exist_ok=False)
base = json.load(open(os.path.join(scene, 'scene.gltf')))
N = 'SPARKY_texture_mixed'


def run(name, g=None, files=None, expect_ok=False, expect=None):
    d = os.path.join(work, name)
    shutil.copytree(scene, d)
    if g is not None:
        json.dump(g, open(os.path.join(d, 'scene.gltf'), 'w'))
    if files:
        gg = json.load(open(os.path.join(d, 'scene.gltf')))
        for rel, text in files.items():
            open(os.path.join(d, rel), 'w').write(text)
            for p in gg['extensions'][N]['procedures']:
                if p['uri'] == rel:
                    p['byteLength'] = len(text.encode())
        json.dump(gg, open(os.path.join(d, 'scene.gltf'), 'w'))
    r = subprocess.run([sys.executable, '-I', tool, 'validate', os.path.join(d, 'scene.gltf')], capture_output=True, text=True)
    ok = r.returncode == 0
    good = ok == expect_ok and (expect is None or expect in r.stdout)
    print('%s %-28s exit %d  %s' % ('PASS' if good else 'FAIL', name, r.returncode, (r.stdout.strip().splitlines() or [''])[-1 if expect_ok else 0][:150]))
    return good


res = [run('as-built', expect_ok=True, expect='valid')]
g = copy.deepcopy(base); g['extensionsUsed'].remove(N); res.append(run('not-in-extensionsUsed', g, expect='extensionsUsed'))
g = copy.deepcopy(base); g['extensionsRequired'] = [N]; res.append(run('in-extensionsRequired', g, expect='extensionsRequired'))
g = copy.deepcopy(base); del g['textures'][0]['source']; res.append(run('no-picture', g, expect='no picture'))
g = copy.deepcopy(base); g['textures'][1]['extensions'][N]['procedure'] = 99; res.append(run('procedure-out-of-range', g, expect='not an index'))
g = copy.deepcopy(base); g['extensions'][N]['procedures'][0]['bufferView'] = 0; res.append(run('uri-and-bufferView', g, expect='exactly one of uri and bufferView'))
g = copy.deepcopy(base); g['extensions'][N]['procedures'][2]['version'] = 2; res.append(run('unknown-language-version', g, expect='version 2 is not known'))
g = copy.deepcopy(base); g['extensions'][N]['version'] = 7; res.append(run('unknown-format-version', g, expect='root version word 7'))
g = copy.deepcopy(base); g['extensions'][N]['procedures'][0]['byteLength'] += 1; res.append(run('wrong-byteLength', g, expect='byteLength'))
txt = open(os.path.join(scene, 'procedures', 'red_brick_03.p2p')).read()
res.append(run('operator-version-unknown', files={'procedures/red_brick_03.p2p': __import__('re').sub(r'^(\S+ Tiles - )\S+', r'\g<1>9', txt, count=1, flags=__import__('re').M)}, expect='Tiles version 9'))
res.append(run('input-undefined', files={'procedures/floor_tiles_06.p2p': 'v0 Noise zz 1 0\nout v0\n'}, expect='not defined above'))
res.append(run('no-out-line', files={'procedures/rock_05.p2p': 'v0 Noise - 1 0 4 4 7 3f666666 0 2 1 3f800000\n'}, expect='no out line'))
v = copy.deepcopy(base)
v['textures'][4]['extensions'][N]['views'] = [{'eye': 'left', 'procedure': 4, 'source': 4}, {'eye': 'left', 'procedure': 5, 'source': 5}]
res.append(run('views-two-lefts', v, expect='"left" and "right" once each'))
v = copy.deepcopy(base)
v['textures'][4]['extensions'][N]['views'] = [{'eye': 'left', 'procedure': 4, 'source': 5}, {'eye': 'right', 'procedure': 5, 'source': 5}]
res.append(run('views-left-not-source', v, expect='left eye\'s picture must be texture.source'))
# the writer's per-eye form: the rock texture with a right eye (the bark's procedure and picture stand in for one:
# a test of the format's fields, not a stereo pair)
d = os.path.join(work, 'writer-views')
shutil.copytree(scene, d)
w = subprocess.run([sys.executable, '-I', tool, 'write', os.path.join(d, 'scene.gltf'), '--texture', 'rock', '--procedure', os.path.join(d, 'procedures', 'rock_05.p2p'),
                    '--right-procedure', os.path.join(d, 'procedures', 'bark_brown_02.p2p'), '--right-picture', os.path.join(d, 'pictures', 'bark_brown_02.jpg')], capture_output=True, text=True)
print('writer:', w.stdout.strip(), w.stderr.strip()[:200])
r = subprocess.run([sys.executable, '-I', tool, 'validate', os.path.join(d, 'scene.gltf')], capture_output=True, text=True)
gv = json.load(open(os.path.join(d, 'scene.gltf')))
views = gv['textures'][4]['extensions'][N].get('views')
good = r.returncode == 0 and views and views[1]['eye'] == 'right'
print('%s writer-views                  exit %d  %s  views=%s' % ('PASS' if good else 'FAIL', r.returncode, r.stdout.strip().splitlines()[-1], json.dumps(views)))
res.append(good)
print('%d of %d as expected' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
