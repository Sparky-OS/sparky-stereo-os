#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""rust-crate-sizes.py BINARY [BINARY...]: bytes of symbols per crate (nm -S -C, Rust v0 names).

Method: every defined symbol with a size is given to the crate its demangled path starts with
(for `<T as Trait>::f` the crate of T; references, pointers, slices and tuples are looked through).
core, alloc and std are counted as "std"; symbols with no Rust path as "(native)".
What symbols do not cover (most of .rodata, .eh_frame, relocation tables) is "(no symbol)",
taken from the file's allocated section sizes. With several binaries it also prints, per crate,
the bytes every binary carries (the minimum across them): the duplicated part.
Writes JSON to stdout.
"""
import json, re, subprocess, sys
STD = {'core', 'alloc', 'std', 'compiler_builtins', 'hashbrown_std', 'std_detect', 'panic_unwind', 'rustc_demangle', 'gimli', 'addr2line', 'object', 'miniz_oxide_std'}


def crate_of(name):
    s = name
    while True:
        s = s.lstrip('<&*([ ')
        m = re.match(r'(?:mut |const |dyn |impl |unsafe |extern "[^"]*" |fn\()', s)
        if not m:
            break
        s = s[m.end():]
    m = re.match(r'([A-Za-z_][A-Za-z0-9_]*)(\[[0-9a-f]+\])?::', s)
    if not m:
        return '(native)'
    c = m[1]
    return 'std' if c in STD else c


def measure(path):
    out = subprocess.run(['nm', '-S', '--defined-only', '-C', path], capture_output=True, text=True, check=True).stdout
    sizes, seen = {}, set()
    for line in out.splitlines():
        m = re.match(r'([0-9a-f]+) ([0-9a-f]+) (\S) (.*)$', line)
        if not m:
            continue
        addr, size = int(m[1], 16), int(m[2], 16)
        if (addr, size) in seen or size == 0:
            continue
        seen.add((addr, size))
        c = crate_of(m[4])
        sizes[c] = sizes.get(c, 0) + size
    sect = subprocess.run(['size', '-A', path], capture_output=True, text=True, check=True).stdout
    alloc = 0
    for line in sect.splitlines():
        p = line.split()
        if len(p) == 3 and p[0].startswith('.') and p[1].isdigit() and int(p[2]) != 0 and p[0] not in ('.bss', '.tbss'):
            alloc += int(p[1])
    sizes['(no symbol)'] = max(0, alloc - sum(sizes.values()))
    return sizes, alloc


if __name__ == '__main__':
    res = {}
    for b in sys.argv[1:]:
        s, alloc = measure(b)
        res[b] = {'allocated': alloc, 'crates': dict(sorted(s.items(), key=lambda kv: -kv[1]))}
    if len(sys.argv) > 2:
        names = set.intersection(*(set(r['crates']) for r in res.values())) - {'(no symbol)'}
        res['carried_by_all'] = dict(sorted(((n, min(r['crates'][n] for r in res.values() if 'crates' in r)) for n in names), key=lambda kv: -kv[1]))
        res['carried_by_all_total'] = sum(res['carried_by_all'].values())
    json.dump(res, sys.stdout, indent=1)
