#!/usr/bin/python3 -I
"""table.py EVIDENCE_DIR: judges the matrix rows of the red (published set) and green (package installed by apt) runs
against what the design says, and prints one line per row with PASS or FAIL. A file whose rate the device takes plays at its
own rate with no conversion (bit for bit on a 24 or 32 bit path); a file it cannot take is converted exactly once, to a rate
the device takes, at the conversion quality of the design (14 on the station's processor)."""
import json, sys

DEVICE_RATES = {'dac': [44100, 48000, 88200, 96000, 176400, 192000], 'only48': [48000], 'pcm16': [44100, 48000],
                'hdmi': [32000, 44100, 48000, 88200, 96000], 'bt': [44100, 48000]}
WIDE = ('dac', 'only48', 'hdmi')       # 24 or 32 bit paths, where bit exactness is checked
QUALITY = 14


def judge(r):
    rates = DEVICE_RATES[r['device']]
    src = r['source_rate']
    why = []
    if 'error' in r:
        return False, [r['error']]
    if src in rates:
        ok = r['graph_rate'] == src and r['device_rate'] == src and not r['resampled']
        if not ok:
            why.append('the device takes %d Hz but the graph runs at %s and the device was opened at %s' % (src, r['graph_rate'], r['device_rate']))
        elif r['device'] in WIDE and r.get('bit_exact') is not True:
            ok = False
            why.append('samples not bit for bit equal: %s' % r.get('samples'))
        elif r['device'] not in WIDE and not (r.get('samples', {}).get('aligned') and r['samples']['max_error_24bit_steps'] <= 384):
            ok = False
            why.append('16 bit samples differ by more than half a step of rounding and one step of dither: %s' % r.get('samples'))
        return ok, why
    one = (r['resampled_at_stream'] != r['resampled_at_device'])
    ok = r['resampled'] and one and r['device_rate'] in rates
    if not ok:
        why.append('expected one conversion to a rate the device takes: graph %s, device %s' % (r['graph_rate'], r['device_rate']))
    q = r['stream_resample_quality'] if r['resampled_at_stream'] else r['sink_props_resample_quality']
    if q != QUALITY:
        ok = False
        why.append('the conversion runs at quality %s, not %d' % (q, QUALITY))
    return ok, why


def main(ev):
    total = {}
    for tag in ('red', 'green'):
        rows = [json.loads(l) for l in open('%s/%s-matrix.jsonl' % (ev, tag))]
        print('== %s: %d rows' % (tag, len(rows)))
        npass = 0
        for r in rows:
            ok, why = judge(r)
            npass += ok
            kind = 'native' if r['source_rate'] in DEVICE_RATES[r['device']] else 'converted'
            print('%-4s %-7s %6d Hz  graph %6s  device %6s %-8s %-9s stream q %-26s %s' % (
                'PASS' if ok else 'FAIL', r['device'], r['source_rate'], r['graph_rate'], r.get('device_rate'), r.get('device_format'),
                kind, r.get('stream_resample_quality'), '; '.join(why)))
        total[tag] = (npass, len(rows))
        print('%s: %d of %d rows follow the design' % (tag, npass, len(rows)))
    return 0 if total['green'][0] == total['green'][1] and total['red'][0] < total['red'][1] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
