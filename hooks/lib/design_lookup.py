#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""design_lookup: find the recorded design for a subject by the CONTENT of the memory files, never by their names.

  design_lookup.py --memory DIR [--also FILE]... [--max-files N] [--lines N] WORD [WORD...]

Each WORD is a case-insensitive regular expression; a file matches when any of them is found in it.
Files are ranked by how many different words they hold, then by how many lines match.
For each file it prints the path, the file's own description line and the first matching lines.
A design kept in a file named after a principle is found this way; a search by file name misses it.
Exit status: 0 with matches, 1 with none, 2 on a usage or setup error.
"""
import argparse
import os
import re
import sys

sys.dont_write_bytecode = True


def description_of(text):
    """The description line of a memory file's header, if it has one."""
    if text.startswith('---\n'):
        end = text.find('\n---', 4)
        for line in text[4:end if end > 0 else len(text)].splitlines():
            if line.startswith('description:'):
                return line.split(':', 1)[1].strip().strip('"\'')
    return ''


def search(memory_dir, words, also=(), index_name='MEMORY.md'):
    """[(matched words, matching lines, path, description, [lines])], best first."""
    patterns = [(w, re.compile(w, re.I)) for w in words]
    files = []
    try:
        names = sorted(os.listdir(memory_dir))
    except OSError as e:
        raise OSError(f'cannot list the memory folder {memory_dir}: {e.strerror}') from e
    for name in names:
        if name.endswith('.md') and name != index_name:
            files.append(os.path.join(memory_dir, name))
    files += [f for f in also if os.path.isfile(f)]
    found = []
    for path in files:
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                text = f.read(2_000_000)
        except OSError:
            continue
        matched, lines = set(), []
        for line in text.splitlines():
            hits = [w for w, rx in patterns if rx.search(line)]
            if hits:
                matched.update(hits)
                lines.append(line.strip())
        if matched:
            found.append((len(matched), len(lines), path, description_of(text), lines, sorted(matched)))
    found.sort(key=lambda r: (-r[0], -r[1], r[2]))
    return found


def report(memory_dir, words, also=(), max_files=8, max_lines=2, width=300):
    found = search(memory_dir, words, also)
    if not found:
        return ''
    out = [f'# Design lookup: {" | ".join(words)}',
           f'{len(found)} file(s) match; read each one named here in full and quote the lines that govern the work.']
    for hits, count, path, description, lines, matched in found[:max_files]:
        out.append(f'- {path}  [{hits} of {len(words)} words: {", ".join(matched)}; {count} line(s)]')
        if description:
            out.append(f'    {description[:width]}')
        out += [f'    > {line[:width]}' for line in lines[:max_lines]]
    if len(found) > max_files:
        out.append(f'- ... {len(found) - max_files} more: ' + ', '.join(os.path.basename(r[2]) for r in found[max_files:max_files + 12]))
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(description='Find the recorded design for a subject by the content of the memory files.')
    ap.add_argument('--memory', required=True, help='the folder of memory files, one fact per file')
    ap.add_argument('--also', action='append', default=[], help='another file to search (a decisions log); may repeat')
    ap.add_argument('--max-files', type=int, default=8)
    ap.add_argument('--lines', type=int, default=2)
    ap.add_argument('words', nargs='+')
    a = ap.parse_args()
    try:
        text = report(a.memory, a.words, a.also, a.max_files, a.lines)
    except (OSError, re.error) as e:
        print(f'design_lookup: {e}', file=sys.stderr)
        return 2
    if not text:
        print(f'design_lookup: nothing in {a.memory} holds {" | ".join(a.words)}; no design found is an answer to report, not to fill in')
        return 1
    print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
