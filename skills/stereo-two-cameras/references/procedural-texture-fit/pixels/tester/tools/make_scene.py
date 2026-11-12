#!/usr/bin/env python3
"""Build the Procedural Texture Rendering demo's scene: a small courtyard in glTF 2.0 whose seven textures each name a
procedure beside their picture (KHR_texture_procedural_rendering, a proposal for glTF), with one model file per
object, one script and one sound, so the page's
detailed view has every kind of scene component.

make_scene.py OUTDIR PICTURES-PPM-DIR PROCEDURES-DIR
  OUTDIR (emptied of what this script writes): scene.gltf, geometry/NAME.bin, pictures/NAME.jpg (JPEG quality 85,
  from the 2048 pixel pictures), procedures/NAME.p2p (each picture's fitted procedure, PROCEDURES-DIR/NAME.script as
  the fitter typed it), scripts/orbit.js, sounds/wind.mp3 (made here from noise, encoded by ffmpeg's libmp3lame), CREDITS.md.
The geometry is ours (planes, boxes, cylinders, a squashed icosphere), written here; the pictures are CC0 (Poly Haven).
Our code, BSD 2-clause."""
import json
import math
import os
import struct
import subprocess
import sys
import wave

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ptr_texture  # noqa: E402

# texture name, picture, its fitted procedure (the script's path under PROCEDURES-DIR), the picture's author
TEXTURES = [
    ('brick wall', 'red_brick_03', 'st/bricks-h.script', 'Rob Tuytel'),
    ('floor tiles', 'floor_tiles_06', 'fit/floor-dark.whole.script', 'Rob Tuytel'),
    ('metal plate', 'metal_plate', 'st/plate-B.script', 'Rob Tuytel'),
    ('terracotta tiles', 'patterned_terracotta_tiling', 'fit/terra-stain.whole.script', 'Amal Kumar'),
    ('rock', 'rock_05', 'grid/rock_05-2x2.script', 'Rob Tuytel'),
    ('bark', 'bark_brown_02', 'grid/bark_brown_02-2x2.script', 'Rob Tuytel'),
    ('rusted metal', 'rusty_metal_02', 'st/rm-s5.script', 'Rob Tuytel'),
]


def plane(p0, du, dv, nrm, uv0=(0, 0), uv1=(1, 1)):
    """a quad from corner p0 along du (u) and dv (v); v runs down the picture as glTF's does (3.8.4)."""
    p0, du, dv = np.array(p0, float), np.array(du, float), np.array(dv, float)
    pos = [p0, p0 + du, p0 + du + dv, p0 + dv]
    uv = [(uv0[0], uv0[1]), (uv1[0], uv0[1]), (uv1[0], uv1[1]), (uv0[0], uv1[1])]
    n = [nrm] * 4
    # counter-clockwise seen from the normal's side (glTF front faces, 3.7.2.1)
    a, b = np.cross(du, dv), np.array(nrm, float)
    idx = [0, 1, 2, 0, 2, 3] if np.dot(a, b) > 0 else [0, 2, 1, 0, 3, 2]
    return pos, n, uv, idx


def merge(parts):
    P, N, T, I = [], [], [], []
    for pos, n, uv, idx in parts:
        base = len(P)
        P += list(pos)
        N += list(n)
        T += list(uv)
        I += [base + i for i in idx]
    return P, N, T, I


def box(x0, y0, z0, x1, y1, z1):
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    return merge([
        plane((x0, y1, z1), (sx, 0, 0), (0, -sy, 0), (0, 0, 1)),     # front, v down the face
        plane((x1, y1, z0), (-sx, 0, 0), (0, -sy, 0), (0, 0, -1)),   # back
        plane((x0, y1, z0), (0, 0, sz), (0, -sy, 0), (-1, 0, 0)),    # left
        plane((x1, y1, z1), (0, 0, -sz), (0, -sy, 0), (1, 0, 0)),    # right
        plane((x0, y1, z0), (sx, 0, 0), (0, 0, sz), (0, 1, 0)),      # top
        plane((x0, y0, z1), (sx, 0, 0), (0, 0, -sz), (0, -1, 0)),    # bottom
    ])


def cylinder(cx, cz, r, h, seg, vscale=1.0):
    P, N, T, I = [], [], [], []
    for k in range(seg + 1):
        a = 2 * math.pi * k / seg
        c, s = math.cos(a), math.sin(a)
        for j, y in enumerate((h, 0.0)):
            P.append((cx + r * c, y, cz + s * r))
            N.append((c, 0, s))
            T.append((k / seg, j * vscale))
    for k in range(seg):
        a, b, c2, d = 2 * k, 2 * k + 1, 2 * k + 2, 2 * k + 3
        I += [a, c2, b, b, c2, d]
    # the top cap, the picture laid flat across it
    base = len(P)
    P.append((cx, h, cz)); N.append((0, 1, 0)); T.append((0.5, 0.5))
    for k in range(seg + 1):
        a = 2 * math.pi * k / seg
        P.append((cx + r * math.cos(a), h, cz + r * math.sin(a))); N.append((0, 1, 0))
        T.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
    for k in range(seg):
        I += [base, base + 2 + k, base + 1 + k]
    return P, N, T, I


def boulder(cx, cy, cz, r, squash, sub=3):
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    V = [np.array(v) / np.linalg.norm(v) for v in V]
    for _ in range(sub):
        mid = {}
        def m(a, b):
            k = (min(a, b), max(a, b))
            if k not in mid:
                v = V[a] + V[b]
                V.append(v / np.linalg.norm(v))
                mid[k] = len(V) - 1
            return mid[k]
        nf = []
        for a, b, c in F:
            ab, bc, ca = m(a, b), m(b, c), m(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = nf
    rng = np.random.default_rng(508)
    bumps = [(rng.normal(size=3), rng.uniform(0.04, 0.12)) for _ in range(9)]
    P, N, T = [], [], []
    for v in V:
        d = 1.0 + sum(a * math.exp(-8 * (1 - np.dot(v, b / np.linalg.norm(b)))) for b, a in bumps)
        p = v * d
        P.append((cx + r * p[0], cy + r * squash * p[1], cz + r * p[2]))
        N.append(tuple(v))
        T.append((0.5 + math.atan2(v[2], v[0]) / (2 * math.pi), math.acos(max(-1, min(1, v[1]))) / math.pi))
    # normals from the faces, for the bumped and squashed shape
    acc = np.zeros((len(P), 3))
    Pa = np.array(P)
    for a, b, c in F:
        n = np.cross(Pa[b] - Pa[a], Pa[c] - Pa[a])
        acc[a] += n; acc[b] += n; acc[c] += n
    acc /= np.linalg.norm(acc, axis=1, keepdims=True)
    N = [tuple(x) for x in acc]
    # glTF front faces are counter-clockwise from outside; the icosphere's faces above are counter-clockwise
    I = [i for f in F for i in f]
    return P, N, T, I


def write_bin(path, P, N, T, I):
    P, N, T = np.asarray(P, '<f4'), np.asarray(N, '<f4'), np.asarray(T, '<f4')
    I = np.asarray(I, '<u2')
    blobs = [P.tobytes(), N.tobytes(), T.tobytes(), I.tobytes()]
    data = b''
    offs = []
    for b in blobs:
        offs.append(len(data))
        data += b + b'\0' * ((4 - len(b) % 4) % 4)
    with open(path, 'wb') as f:
        f.write(data)
    return data, offs, [len(b) for b in blobs], P, I


def main():
    out, pics, procs = sys.argv[1], sys.argv[2], sys.argv[3]
    for d in ('geometry', 'pictures', 'procedures', 'scripts', 'sounds'):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    g = {'asset': {'version': '2.0', 'generator': 'make_scene.py and ptr_texture.py (Procedural Texture Rendering)',
                   'copyright': 'geometry, script and sound: CC0 1.0; pictures: CC0 1.0 (Poly Haven), see CREDITS.md'},
         'extensionsUsed': ['KHR_lights_punctual', 'KHR_audio_emitter'],
         'scene': 0, 'scenes': [{'name': 'Courtyard', 'nodes': []}], 'nodes': [], 'meshes': [], 'materials': [],
         'buffers': [], 'bufferViews': [], 'accessors': [], 'textures': [], 'images': [],
         'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}]}

    # pictures as JPEG, textures with their pictures
    for name, pic, _, _ in TEXTURES:
        jpg = os.path.join(out, 'pictures', pic + '.jpg')
        Image.open(os.path.join(pics, pic + '.ppm')).convert('RGB').save(jpg, quality=85, optimize=True)
        ii = ptr_texture.add_image(g, out, jpg, name + ' picture')
        g['textures'].append({'name': name, 'sampler': 0, 'source': ii})
        metallic = 0.6 if 'metal' in name else 0.0
        g['materials'].append({'name': name, 'pbrMetallicRoughness': {
            'baseColorTexture': {'index': len(g['textures']) - 1}, 'metallicFactor': metallic, 'roughnessFactor': 0.85}})
    # the procedures: each texture names its procedure beside its picture
    for ti, (name, pic, script, _) in enumerate(TEXTURES):
        dst = os.path.join(out, 'procedures', pic + '.p2p')
        with open(os.path.join(procs, script), encoding='utf-8') as f:
            text = f.read()
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(text)
        pi = ptr_texture.add_procedure(g, out, dst, name + ' procedure')
        ptr_texture.attach_procedure(g, ti, pi)

    models = [
        ('floor', 1, merge([plane((-2, 0, -2), (4, 0, 0), (0, 0, 4), (0, 1, 0))])),
        ('wall', 0, merge([plane((-2, 2, -2), (4, 0, 0), (0, -2, 0), (0, 0, 1), (0, 0), (1, 0.5))])),
        ('crate', 2, box(-1.65, 0, -0.75, -0.85, 0.8, 0.05)),
        ('plinth', 3, box(0.35, 0, -1.75, 1.65, 0.35, -0.85)),
        ('boulder', 4, boulder(-0.1, 0.28, 0.45, 0.45, 0.65, 2)),
        ('tree trunk', 5, cylinder(-1.55, -1.5, 0.22, 2.4, 24, 1.0)),
        ('barrel', 6, cylinder(1.3, 0.55, 0.3, 0.9, 24, 1.0)),
    ]
    for mname, mat, (P, N, T, I) in models:
        fname = 'geometry/%s.bin' % mname.replace(' ', '-')
        data, offs, lens, Pa, Ia = write_bin(os.path.join(out, fname), P, N, T, I)
        bi = len(g['buffers'])
        g['buffers'].append({'name': mname + ' geometry', 'uri': fname, 'byteLength': len(data)})
        acc = []
        for k, (ln, typ, comp, cnt, target) in enumerate([
                (lens[0], 'VEC3', 5126, len(P), 34962), (lens[1], 'VEC3', 5126, len(P), 34962),
                (lens[2], 'VEC2', 5126, len(P), 34962), (lens[3], 'SCALAR', 5123, len(I), 34963)]):
            g['bufferViews'].append({'buffer': bi, 'byteOffset': offs[k], 'byteLength': ln, 'target': target})
            a = {'bufferView': len(g['bufferViews']) - 1, 'componentType': comp, 'count': cnt, 'type': typ}
            if k == 0:
                a['min'] = [float(x) for x in Pa.min(axis=0)]
                a['max'] = [float(x) for x in Pa.max(axis=0)]
            g['accessors'].append(a)
            acc.append(len(g['accessors']) - 1)
        g['meshes'].append({'name': mname, 'primitives': [{'attributes': {'POSITION': acc[0], 'NORMAL': acc[1], 'TEXCOORD_0': acc[2]},
                                                           'indices': acc[3], 'material': mat}]})
        g['nodes'].append({'name': mname, 'mesh': len(g['meshes']) - 1})
        g['scenes'][0]['nodes'].append(len(g['nodes']) - 1)

    # the camera, the light (KHR_lights_punctual), the script's node to turn
    eye, at = np.array([0.0, 2.05, 4.9]), np.array([0.0, 0.45, -0.6])
    f = at - eye
    f /= np.linalg.norm(f)
    pitch = math.asin(f[1])
    q = (math.sin(pitch / 2), 0.0, 0.0, math.cos(pitch / 2))      # about +X: a camera looks down -Z (3.10.3)
    g['cameras'] = [{'name': 'view', 'type': 'perspective', 'perspective': {'yfov': math.radians(42), 'znear': 0.05, 'zfar': 50, 'aspectRatio': 16 / 9}}]
    g['nodes'].append({'name': 'view', 'camera': 0, 'translation': [float(x) for x in eye], 'rotation': list(q)})
    cam = len(g['nodes']) - 1
    g['nodes'].append({'name': 'orbit', 'children': [cam]})
    g['scenes'][0]['nodes'].append(len(g['nodes']) - 1)
    g['extensions'] = g.get('extensions', {})
    g['extensions']['KHR_lights_punctual'] = {'lights': [{'name': 'sun', 'type': 'directional', 'color': [1.0, 0.97, 0.9], 'intensity': 2.5}]}
    ang = (math.radians(-50), math.radians(-35))
    qx = (math.sin(ang[0] / 2), 0, 0, math.cos(ang[0] / 2))
    qy = (0, math.sin(ang[1] / 2), 0, math.cos(ang[1] / 2))
    qq = (qy[3] * qx[0], qy[1] * qx[3], -qy[1] * qx[0], qy[3] * qx[3])
    g['nodes'].append({'name': 'sun', 'rotation': [float(x) for x in qq], 'extensions': {'KHR_lights_punctual': {'light': 0}}})
    g['scenes'][0]['nodes'].append(len(g['nodes']) - 1)

    # the script: glTF has no place for program code (KHR_interactivity is a behaviour graph), so the scene names it
    # in extras, glTF's place for application-specific data (3.12); the field name url is X3D's Script node's
    with open(os.path.join(out, 'scripts', 'orbit.js'), 'w', encoding='utf-8') as fs:
        fs.write("""// The courtyard's script: turns the node "orbit" (the camera's parent) slowly left and right about the
// courtyard's centre, 25 degrees each way in 24 seconds. The tester calls update(scene, seconds) every frame.
// CC0 1.0.
export function update(scene, t) {
  const n = scene.nodeByName('orbit');
  if (!n) return;
  const a = (25 * Math.PI / 180) * Math.sin(2 * Math.PI * t / 24);
  n.rotation = [0, Math.sin(a / 2), 0, Math.cos(a / 2)];
}
""")
    g['extras'] = {'scripts': [{'name': 'camera orbit', 'url': 'scripts/orbit.js', 'type': 'module'}]}

    # the sound: four seconds of soft wind (noise through a slow low-pass), mono 22.05 kHz, MP3 (KHR_audio_emitter's
    # base type audio/mpeg)
    rate, sec = 22050, 4
    rng = np.random.default_rng(508)
    x = rng.normal(size=rate * sec)
    y = np.zeros_like(x)
    a = 0.0
    for i in range(len(x)):
        k = 0.02 + 0.015 * math.sin(2 * math.pi * i / (rate * 2.0))
        a += k * (x[i] - a)
        y[i] = a
    y *= 0.35 / np.abs(y).max()
    fade = int(0.3 * rate)
    y[:fade] *= np.linspace(0, 1, fade)
    y[-fade:] *= np.linspace(1, 0, fade)
    wav = os.path.join(out, 'sounds', 'wind.wav')
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes((y * 32767).astype('<i2').tobytes())
    mp3 = os.path.join(out, 'sounds', 'wind.mp3')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', wav, '-codec:a', 'libmp3lame', '-b:a', '32k', mp3], check=True)
    os.remove(wav)
    g['extensionsUsed'].append('KHR_audio_emitter') if 'KHR_audio_emitter' not in g['extensionsUsed'] else None
    g['extensions']['KHR_audio_emitter'] = {
        'audio': [{'name': 'wind', 'uri': 'sounds/wind.mp3', 'mimeType': 'audio/mpeg'}],
        'sources': [{'name': 'wind', 'gain': 0.5, 'autoplay': True, 'loop': True, 'audio': 0}],
        'emitters': [{'name': 'wind', 'type': 'global', 'gain': 1.0, 'sources': [0]}]}
    g['scenes'][0]['extensions'] = {'KHR_audio_emitter': {'emitters': [0]}}
    # keep the extension's root object last in extensions and in extensionsUsed's order of first use
    ptr_texture.save(os.path.join(out, 'scene.gltf'), g)
    # every picture's, script's and sound's size, so a page can total the scene before it downloads anything
    ptr_texture.write_sizes(os.path.join(out, 'scene.gltf'))

    with open(os.path.join(out, 'CREDITS.md'), 'w', encoding='utf-8') as fc:
        fc.write('# Credits of the courtyard scene\n\n')
        fc.write('The pictures are CC0 1.0 from Poly Haven (polyhaven.com/license), each by its author as Poly Haven records it:\n\n')
        for name, pic, _, who in TEXTURES:
            fc.write('- %s: `%s` by %s, the 2K diffuse PNG, here at 2048 pixels as JPEG quality 85.\n' % (name, pic, who))
        fc.write('\nThe procedures were found from those pictures\' pixels by a fitting program, with new operators in the way of Farbrausch\'s werkkzeug3.\n')
        fc.write('The geometry, the script and the sound (made from noise) are ours, CC0 1.0.\n')
    print('scene written to %s' % out)
    for level, text in ptr_texture.validate(os.path.join(out, 'scene.gltf')):
        print('%s: %s' % (level, text))


if __name__ == '__main__':
    main()
