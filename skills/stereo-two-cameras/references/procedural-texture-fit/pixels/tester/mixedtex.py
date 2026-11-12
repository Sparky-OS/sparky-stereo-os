#!/usr/bin/env python3
"""The mixed texture (ORDER 508, milestone 3): one glTF 2.0 texture that carries a procedure and a picture.

The texture keeps its ordinary picture in `texture.source` (glTF 2.0, 3.8.2), so a viewer that ignores the extension
shows the picture. The extension object on the texture names a procedure in the root extension's `procedures` array;
a procedure is referenced as an image is (glTF 2.0, 5.18: a `uri`, or a `bufferView` with a `mimeType`), with its
language and its version word. An optional `views` array carries one procedure and one picture per eye (the eye names
are WebXR's XREye values, "left" and "right"); the left eye's pair is the texture's own, so a 2D viewer shows the
left eye. The specification page is MIXED-TEXTURE.md beside this file. The extension's name is a working name.

mixedtex.py write SCENE.gltf --texture NAME|INDEX --procedure FILE [--procedure-name TEXT]
                 [--right-procedure FILE --right-picture IMAGE]
    adds the procedure FILE (copied beside the scene under procedures/ unless it already lies under the scene's folder)
    to the texture, and with --right-* the right eye's pair; the file is rewritten in place.
mixedtex.py validate SCENE.gltf [--no-files]
    checks the extension's rules and each procedure's text; prints one line per finding; exit 1 on any error.

Outside input is data: the procedure text is parsed, never run; paths stay under the scene's folder.
Our code, BSD 2-clause."""
import argparse
import json
import os
import re
import shutil
import sys

NAME = 'SPARKY_texture_mixed'      # working name: the prefix is not registered (glTF extensions/Prefixes.md)
FORMAT_VERSION = 1                 # the extension object's own version word
LANGUAGES = {'p2p': {1}}           # procedure languages and the version words a reader of this version knows

# The modern operators and the highest version word each one draws (src/ops/NAME.zig, the "version" row of each
# parameter table, read 2026-11-11); a werkkzeug3 operator (Flat, Text, Blur ...) carries no version word.
MODERN = {'Noise': 1, 'Cells': 2, 'Tiles': 4, 'Ramp': 1, 'Layer': 2, 'Shade': 2, 'Scatter': 2, 'Wear': 1,
          'Tint': 1, 'Quad': 1, 'Grid': 1, 'Stack': 1}
WERKKZEUG3 = {'Flat', 'Perlin', 'Cell', 'Gradient', 'Bricks', 'Color', 'Range', 'HSCB', 'Blur', 'Sharpen', 'GlowRect',
              'GlowRectOld', 'Dots', 'Transform', 'TransformMul', 'Twirl', 'Normals', 'Light', 'ColorBalance', 'Unwrap',
              'Bulge', 'Merge', 'Distort', 'Bump', 'Paste', 'Mask', 'Format', 'Pass', 'Text'}   # p2p.zig's table
EYES = ('left', 'right')
LINE_ID = re.compile(r'^[A-Za-z0-9_.-]{1,32}$')
HEX = re.compile(r'^[0-9a-fA-F]{1,8}$')


def parse_procedure(text):
    """The p2p script: lines `ID OP INPUTS WORDS...` (INPUTS '-' or ID,ID...; WORDS hexadecimal 32-bit words or s=TEXT
    strings), comments after '#', one `out ID` line. Returns (nodes, root id, problems)."""
    problems = []
    nodes = {}
    order = []
    root = None
    for k, raw in enumerate(text.split('\n'), 1):
        t = raw.split()
        if not t or t[0].startswith('#'):
            continue
        if t[0] == 'out':
            if len(t) != 2 or t[1] not in nodes:
                problems.append('line %d: the out line names no operator defined above it' % k)
            else:
                root = t[1]
            continue
        if len(t) < 3 or not LINE_ID.match(t[0]):
            problems.append('line %d: not an operator line' % k)
            continue
        nid, op, ins = t[0], t[1], t[2]
        if nid in nodes:
            problems.append('line %d: %s is defined twice' % (k, nid))
        inputs = [] if ins == '-' else ins.split(',')
        for i in inputs:
            if i not in nodes:
                problems.append('line %d: input %s of %s is not defined above it' % (k, i, nid))
        words = [w for w in t[3:] if not w.startswith('s=')]
        for w in words:
            if not HEX.match(w):
                problems.append('line %d: %s is not a 32-bit hexadecimal word' % (k, w))
                break
        if op in MODERN:
            if not words:
                problems.append('line %d: %s has no version word' % (k, op))
            elif HEX.match(words[0]):
                v = int(words[0], 16)
                if v < 1 or v > MODERN[op]:
                    problems.append('line %d: %s version %d is not known to this reader (it knows 1 to %d)' % (k, op, v, MODERN[op]))
        elif op not in WERKKZEUG3:
            problems.append('line %d: operator %s is not known to this reader' % (k, op))
        nodes[nid] = (op, inputs, words)
        order.append(nid)
    if root is None:
        problems.append('no out line')
    return nodes, root, problems


def operators_of(text):
    nodes, _, _ = parse_procedure(text)
    return [v[0] for v in nodes.values()]


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save(path, g):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(g, f, separators=(',', ':'), ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, path)


def use_extension(g):
    used = g.setdefault('extensionsUsed', [])
    if NAME not in used:
        used.append(NAME)
    root = g.setdefault('extensions', {}).setdefault(NAME, {})
    root.setdefault('version', FORMAT_VERSION)
    return root.setdefault('procedures', [])


def add_procedure(g, scene_dir, file, name, language='p2p', version=1):
    """Copy FILE beside the scene (procedures/BASENAME) unless it is already under scene_dir; return its index."""
    procs = use_extension(g)
    src = os.path.realpath(file)
    base = os.path.realpath(scene_dir)
    if os.path.commonpath([src, base]) == base:
        rel = os.path.relpath(src, base)
    else:
        rel = os.path.join('procedures', os.path.basename(file))
        os.makedirs(os.path.join(scene_dir, 'procedures'), exist_ok=True)
        shutil.copyfile(src, os.path.join(scene_dir, rel))
    with open(os.path.join(scene_dir, rel), encoding='utf-8') as f:
        text = f.read()
    _, _, problems = parse_procedure(text)
    if problems:
        raise SystemExit('%s: %s' % (file, '; '.join(problems)))
    rel = rel.replace(os.sep, '/')
    for i, p in enumerate(procs):
        if p.get('uri') == rel:
            return i
    procs.append({'name': name, 'uri': rel, 'language': language, 'version': version,
                  'byteLength': len(text.encode('utf-8'))})
    return len(procs) - 1


def add_image(g, scene_dir, file, name):
    src = os.path.realpath(file)
    base = os.path.realpath(scene_dir)
    if os.path.commonpath([src, base]) == base:
        rel = os.path.relpath(src, base)
    else:
        rel = os.path.join('pictures', os.path.basename(file))
        os.makedirs(os.path.join(scene_dir, 'pictures'), exist_ok=True)
        shutil.copyfile(src, os.path.join(scene_dir, rel))
    rel = rel.replace(os.sep, '/')
    ext = rel.rsplit('.', 1)[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}.get(ext)
    if not mime:
        raise SystemExit('%s: glTF 2.0 pictures are JPEG or PNG (3.8.3)' % file)
    images = g.setdefault('images', [])
    for i, im in enumerate(images):
        if im.get('uri') == rel:
            return i
    images.append({'name': name, 'uri': rel, 'mimeType': mime})
    return len(images) - 1


def make_mixed(g, texture, procedure, right=None):
    """texture: index; procedure: index; right: (procedure index, image index) for the right eye, or None."""
    t = g['textures'][texture]
    if 'source' not in t:
        raise SystemExit('texture %d has no picture (texture.source): a mixed texture keeps its picture there' % texture)
    ext = {'procedure': procedure}
    if right is not None:
        ext['views'] = [{'eye': 'left', 'procedure': procedure, 'source': t['source']},
                        {'eye': 'right', 'procedure': right[0], 'source': right[1]}]
    t.setdefault('extensions', {})[NAME] = ext


def find_texture(g, key):
    texs = g.get('textures', [])
    if key.isdigit() and int(key) < len(texs):
        return int(key)
    for i, t in enumerate(texs):
        if t.get('name') == key:
            return i
    raise SystemExit('no texture named %s' % key)


def validate(path, files=True):
    """[(level, text)], level 'error' or 'note'."""
    out = []
    err = lambda s: out.append(('error', s))
    note = lambda s: out.append(('note', s))
    try:
        g = load(path)
    except (OSError, ValueError) as e:
        return [('error', 'cannot read the scene: %s' % e)]
    scene_dir = os.path.dirname(os.path.abspath(path))
    used = g.get('extensionsUsed', [])
    req = g.get('extensionsRequired', [])
    root = g.get('extensions', {}).get(NAME)
    textures = g.get('textures', [])
    images = g.get('images', [])
    mixed = [(i, t['extensions'][NAME]) for i, t in enumerate(textures) if NAME in t.get('extensions', {})]
    if not mixed and root is None:
        note('no mixed texture in this scene')
        return out
    if NAME not in used:
        err('%s is used but not listed in extensionsUsed (glTF 2.0, 3.12: all extensions used MUST be listed)' % NAME)
    if root is None:
        err('the root extension object (with its procedures array) is missing')
        return out
    if root.get('version') != FORMAT_VERSION:
        err('root version word %r is not known to this reader (it knows %d)' % (root.get('version'), FORMAT_VERSION))
    procs = root.get('procedures')
    if not isinstance(procs, list) or not procs:
        err('procedures must be a non-empty array')
        procs = []
    for k, p in enumerate(procs):
        where = 'procedure %d (%s)' % (k, p.get('name', 'unnamed'))
        has_uri, has_bv = 'uri' in p, 'bufferView' in p
        if has_uri == has_bv:
            err('%s: exactly one of uri and bufferView (as glTF 2.0 5.18 says for an image)' % where)
        if has_bv and 'mimeType' not in p:
            err('%s: a bufferView needs its mimeType (as for an image)' % where)
        lang, ver = p.get('language'), p.get('version')
        if lang not in LANGUAGES:
            err('%s: language %r is not known to this reader' % (where, lang))
        elif ver not in LANGUAGES[lang]:
            err('%s: %s version %r is not known to this reader (it knows %s)' % (where, lang, ver, sorted(LANGUAGES[lang])))
        text = None
        if has_uri and files:
            uri = p['uri']
            if uri.startswith('data:') or '://' in uri:
                note('%s: %s not checked here (only relative files are read)' % (where, uri[:40]))
            else:
                full = os.path.realpath(os.path.join(scene_dir, uri))
                if os.path.commonpath([full, os.path.realpath(scene_dir)]) != os.path.realpath(scene_dir):
                    err('%s: %s points outside the scene\'s folder' % (where, uri))
                elif not os.path.isfile(full):
                    err('%s: %s does not exist' % (where, uri))
                else:
                    with open(full, 'rb') as f:
                        data = f.read()
                    if 'byteLength' in p and p['byteLength'] != len(data):
                        err('%s: byteLength %d, the file has %d bytes' % (where, p['byteLength'], len(data)))
                    text = data.decode('utf-8', errors='replace')
        if text is not None and lang == 'p2p':
            _, _, problems = parse_procedure(text)
            for pr in problems:
                err('%s: %s' % (where, pr))
    for i, ext in mixed:
        t = textures[i]
        where = 'texture %d (%s)' % (i, t.get('name', 'unnamed'))
        if 'source' not in t:
            err('%s: no picture in texture.source; a viewer that ignores %s would have no picture (glTF 2.0 3.8.2)' % (where, NAME))
        elif not (0 <= t['source'] < len(images)):
            err('%s: texture.source %r is not an image' % (where, t['source']))
        pi = ext.get('procedure')
        if not isinstance(pi, int) or not (0 <= pi < len(procs)):
            err('%s: procedure %r is not an index into the procedures array' % (where, pi))
        views = ext.get('views')
        if views is not None:
            if not isinstance(views, list) or len(views) != 2:
                err('%s: views holds exactly two entries, one per eye' % where)
            else:
                eyes = [v.get('eye') for v in views]
                if sorted(eyes) != sorted(EYES):
                    err('%s: views must name the eyes "left" and "right" once each (WebXR XREye), not %s' % (where, eyes))
                for v in views:
                    if not isinstance(v.get('procedure'), int) or not (0 <= v['procedure'] < len(procs)):
                        err('%s: the %s eye\'s procedure %r is not an index into procedures' % (where, v.get('eye'), v.get('procedure')))
                    if not isinstance(v.get('source'), int) or not (0 <= v['source'] < len(images)):
                        err('%s: the %s eye\'s source %r is not an image' % (where, v.get('eye'), v.get('source')))
                    if v.get('eye') == 'left':
                        if v.get('source') != t.get('source'):
                            err('%s: the left eye\'s picture must be texture.source, so a 2D viewer shows the left eye' % where)
                        if v.get('procedure') != pi:
                            err('%s: the left eye\'s procedure must be the texture\'s procedure' % where)
    if NAME in req:
        if all('source' in textures[i] for i, _ in mixed):
            err('%s is in extensionsRequired, so a viewer that ignores it refuses the scene although every mixed texture has its picture; list it in extensionsUsed only' % NAME)
    if files:
        for k, im in enumerate(images):
            uri = im.get('uri')
            if uri and not uri.startswith('data:') and '://' not in uri and not os.path.isfile(os.path.join(scene_dir, uri)):
                err('image %d (%s): %s does not exist' % (k, im.get('name', 'unnamed'), uri))
    if not any(l == 'error' for l, _ in out):
        note('%d mixed texture(s), %d procedure(s), %d picture(s): valid' % (len(mixed), len(procs), len(images)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    w = sub.add_parser('write')
    w.add_argument('scene')
    w.add_argument('--texture', required=True)
    w.add_argument('--procedure', required=True)
    w.add_argument('--procedure-name')
    w.add_argument('--right-procedure')
    w.add_argument('--right-picture')
    v = sub.add_parser('validate')
    v.add_argument('scene')
    v.add_argument('--no-files', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'write':
        if bool(a.right_procedure) != bool(a.right_picture):
            raise SystemExit('the right eye needs both --right-procedure and --right-picture')
        g = load(a.scene)
        d = os.path.dirname(os.path.abspath(a.scene))
        ti = find_texture(g, a.texture)
        name = a.procedure_name or (g['textures'][ti].get('name', 'texture %d' % ti) + ' procedure')
        pi = add_procedure(g, d, a.procedure, name)
        right = None
        if a.right_procedure:
            rp = add_procedure(g, d, a.right_procedure, name + ' (right eye)')
            ri = add_image(g, d, a.right_picture, g['textures'][ti].get('name', 'texture') + ' picture (right eye)')
            right = (rp, ri)
        make_mixed(g, ti, pi, right)
        save(a.scene, g)
        print('texture %d (%s): procedure %d%s' % (ti, g['textures'][ti].get('name', ''), pi, ', right eye %d, %d' % right if right else ''))
        return 0
    findings = validate(a.scene, files=not a.no_files)
    for level, text in findings:
        print('%s: %s' % (level, text))
    return 1 if any(l == 'error' for l, _ in findings) else 0


if __name__ == '__main__':
    sys.exit(main())
