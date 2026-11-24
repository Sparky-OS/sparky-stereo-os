#!/usr/bin/env python3
"""One line per session folder (traced-xwayland-session.sh): whole or red, the error, explicit-sync counts, and for a red case
the last requests Xwayland sent on the surface that got the error.
Usage: explicit-sync-verdict.py CASE_DIR... (prints TSV: case, verdict, errors, acquire points, syncobj surfaces, client's last line)"""
import lzma
import re
import sys
from pathlib import Path

ERR = 'explicit sync is used, but no acquire point is set'


def case(d: Path):
    log = ''
    if (d / 'kwin.log').exists():
        log = (d / 'kwin.log').read_text(errors='replace')
    elif (d / 'kwin.log.xz').exists():
        log = lzma.open(d / 'kwin.log.xz', 'rt', errors='replace').read()
    client = (d / 'client.txt').read_text(errors='replace') if (d / 'client.txt').exists() else ''
    errors = log.count('XWAYLAND: wp_linux_drm_syncobj_surface_v1') + log.count(f'XWAYLAND: {ERR}')
    broke = 'The X11 connection broke' in log
    acquire = len(re.findall(r'wp_linux_drm_syncobj_surface_v1#\d+\.set_acquire_point', log))
    surfaces = len(re.findall(r'wp_linux_drm_syncobj_manager_v1#\d+\.get_surface', log))
    verdict = 'red' if (ERR in log or broke) else 'whole'
    last = [l for l in client.strip().splitlines() if l.strip()][-1:] or ['']
    tail = ''
    m = re.search(r'wl_display#1\.error\(wp_linux_drm_syncobj_surface_v1#(\d+)', log)
    if m:
        sync_id = m.group(1)
        surf = re.search(rf'get_surface\(new id wp_linux_drm_syncobj_surface_v1#{sync_id}, wl_surface#(\d+)\)', log)
        sid = surf.group(1) if surf else None
        lines = [l for l in log.splitlines() if ' -> ' in l and (
            f'wp_linux_drm_syncobj_surface_v1#{sync_id}.' in l or (sid and f'wl_surface#{sid}.' in l))]
        tail = ' | '.join(re.sub(r'^\[([0-9:.]+)\].*?-> ', r'\1 ', l).strip() for l in lines[-5:])
    return [d.name, verdict, str(errors), str(acquire), str(surfaces), last[0][:80], tail]


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        print('\t'.join(case(Path(arg))))
