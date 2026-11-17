#!/usr/bin/env python3
"""Render the Studio's known CC0 camera fixture and measure native PNS views."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

import numpy as np
from PIL import Image


def views(path, n):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    marks = []
    while pos < len(data):
        size = struct.unpack('>I', data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + size]
        crc = struct.unpack('>I', data[pos + 8 + size:pos + 12 + size])[0]
        assert zlib.crc32(tag + body) == crc
        if tag == b'sTER':
            marks.append(body)
        pos += size + 12
    assert marks == [b'\x01']
    image = np.array(Image.open(path).convert('RGBA'))
    right = ((n + 7) // 8) * 8
    assert image.shape[:2] == (n, right + n)
    return image[:, :n], image[:, right:right + n]


def measure(left, right, camera):
    points = []
    f, e, d, t = [camera[key] for key in ['focalPixels', 'separation', 'distance', 'translation']]
    assert abs(f * e * (1 / (d - (-t) - t) - 1 / d)) < 1e-10
    for channel, z in [(0, .5), (2, -.5)]:
        edges = []
        for image in [left, right]:
            rgb = image[..., :3].astype(int)
            other = np.max(np.delete(rgb, channel, axis=2), axis=2)
            ys, xs = np.nonzero((rgb[..., channel] > 20) & (rgb[..., channel] > 2 * other + 5) & (image[..., 3] > 0))
            assert len(xs), 'The known witness is not visible'
            edges.append((int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())))
        a, b = edges
        measured = (a[0] + a[1] - b[0] - b[1]) / 2
        vertical = [a[2] - b[2], a[3] - b[3]]
        prediction = f * e * (1 / (d - z - t) - 1 / d)
        assert -10 - 1e-8 <= prediction <= 4 + 1e-8
        assert -10 <= measured <= 4, 'Measured witness exceeds the default limits'
        points.append({'point': 'nearest' if channel == 0 else 'farthest', 'expected': prediction,
                       'measured': measured, 'verticalEdges': vertical, 'absoluteError': abs(measured - prediction)})
    return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', required=True, type=Path)
    parser.add_argument('--fixture', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expect-renderer', required=True, help='Required substring of the actual OpenGL renderer')
    parser.add_argument('--red', action='store_true', help='Check existing flat views against the stereo prediction; expect exit 1')
    args = parser.parse_args()
    sizes = [8, 16, 22, 24, 32, 48, 64, 128, 256]
    if not args.red:
        args.output.mkdir(parents=True, exist_ok=False)
        for placement, depth, flat in [('screen', 0, 0), ('sunk', -.25, 0), ('popped', .25, 0), ('flat', 0, 1)]:
            for n in sizes:
                folder = args.output / placement / str(n)
                folder.mkdir(parents=True)
                result = subprocess.run([str(args.renderer.resolve()), str(args.fixture.resolve()), str(folder.resolve()),
                                         str(n), str(depth), '10', '4', '1920', '0', str(flat), '1'],
                                        capture_output=True, text=True, check=True)
                camera = json.loads(result.stdout)
                (folder / 'camera.json').write_text(json.dumps(camera, indent=2) + '\n')
                (folder / 'renderer.log').write_text(result.stderr)
    rows = []
    for placement in (['flat'] if args.red else ['screen', 'sunk', 'popped', 'flat']):
        for n in sizes:
            folder = args.output / placement / str(n)
            actual = json.loads((folder / 'camera.json').read_text())
            renderer = next(line for line in actual['capabilities'].splitlines() if 'OpenGL renderer string' in line)
            assert args.expect_renderer in renderer, renderer
            left, right = views(folder / 'pair.pns', n)
            if placement == 'flat':
                assert np.array_equal(left, right), 'One-camera views are unequal'
            expected = json.loads((args.output / 'screen' / str(n) / 'camera.json').read_text()) if args.red else actual
            if placement in ['sunk', 'popped']:
                assert abs(round(actual['centre'])) >= 1
                assert actual['centre'] < 0 if placement == 'sunk' else actual['centre'] > 0
            rows.append({'size': n, 'placement': placement, 'renderer': renderer, 'points': measure(left, right, expected)})
    passed = all(p['absoluteError'] <= 1 and p['verticalEdges'] == [0, 0] for row in rows for p in row['points'])
    result = {'passed': passed, 'rows': rows}
    if args.red:
        print(json.dumps(result, indent=2))
        return 0 if passed else 1
    assert passed, result
    command = [sys.executable, __file__, '--renderer', str(args.renderer), '--fixture', str(args.fixture),
               '--output', str(args.output), '--expect-renderer', args.expect_renderer, '--red']
    red = subprocess.run(command, capture_output=True, text=True)
    assert red.returncode == 1 and json.loads(red.stdout)['passed'] is False, red.stderr
    (args.output / 'negative-control.json').write_text(red.stdout)
    (args.output / 'measurements.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'cases': len(rows), 'points': sum(len(row['points']) for row in rows),
                      'maxAbsoluteError': max(p['absoluteError'] for row in rows for p in row['points']), 'negativeExit': red.returncode}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
