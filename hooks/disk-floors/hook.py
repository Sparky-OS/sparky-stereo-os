#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""disk-floors: free space is said in GiB against each folder's floor before a command that fills a disk.

Before a shell command that asks about disk space or writes a lot (a copy, a clone, an image pull, an unpack), the
free space of every configured folder is shown, lowest first, each against its floor.
While a folder is under its floor, the same is said on any shell command, at most once every few minutes.
What happens to a write-shaped command under a floor is the configuration's choice: told ("context", the default),
put to the person ("ask") or refused ("deny"). README.md beside this file has the configuration and the reasons.
"""
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import hookkit  # noqa: E402

# Each pattern is tried at the start of every simple command of the shell line (the program and its first words).
ASKS = [r'df\b', r'du\b', r'lsblk\b', r'findmnt\b']
WRITES = [r'cp\s+-[a-zA-Z]*[rRa]', r'rsync\b', r'dd\s+.*\bif=', r'git\s+(?:-C\s+\S+\s+)?clone\b', r'(?:docker|podman)\s+(?:image\s+)?(?:pull|build|load|import)\b',
          r'tar\s+-?[a-zA-Z]*x', r'unzip\b', r'debootstrap\b', r'mmdebstrap\b', r'dpkg-buildpackage\b', r'wget\b',
          r'curl\b.*\s-[a-zA-Z]*[oO]\b', r'fallocate\b', r'truncate\b']
GIB = 1 << 30


def measure(floors):
    """[(free GiB, floor GiB, folder)], the folders under their floor first, then lowest free first; a folder that
    cannot be measured is told apart."""
    rows, missing = [], []
    for folder, floor in floors.items():
        try:
            st = os.statvfs(folder)
        except OSError as e:
            missing.append(f'{folder} ({e.strerror})')
            continue
        rows.append((st.f_bavail * st.f_frsize / GIB, float(floor), folder))
    rows.sort(key=lambda r: (r[0] >= r[1], r[0], r[2]))
    return rows, missing


def report(rows, missing):
    def number(floor):
        return f'{floor:.0f}' if floor == int(floor) else f'{floor}'

    parts = [f'{folder} {free:.1f}' + (f' UNDER its floor of {number(floor)}' if free < floor else f' (floor {number(floor)})')
             for free, floor, folder in rows]
    text = 'Disk floors, GiB free, lowest first: ' + '; '.join(parts) + '.'
    if missing:
        text += ' Not measured: ' + '; '.join(missing) + '.'
    return text


def handle(event, kit):
    if event.kind != 'before-tool' or event.tool != 'shell':
        return None
    floors = kit.cfg.get('floors_gib') or {}
    if not floors:
        raise hookkit.HookError(f'no floors: list each folder and its floor under "floors_gib" in {kit.config_path}')
    acting = event.acting_command()
    commands = event.commands()
    lines = [' '.join(words) for words in commands] if commands is not None else None

    def shaped(patterns):
        if lines is None:  # not readable as shell: look for the words anywhere
            return any(re.search(r'\b' + r, acting) for r in patterns)
        return any(re.match(r, line) for r in patterns for line in lines)

    asks = shaped(kit.cfg.get('asks', ASKS))
    writes = shaped(kit.cfg.get('writes', WRITES))
    rows, missing = measure(floors)
    under = [r for r in rows if r[0] < r[1]]
    text = report(rows, missing)
    if under:
        advice = (' Free what this work made (its scratch folders, its containers and images, by name) before writing more; '
                  'never free space by moving work to a disk that may go away.')
        choice = kit.cfg.get('below_floor', 'context')
        if writes and choice in ('ask', 'deny'):
            kit.log('refused.log' if choice == 'deny' else 'asked.log', f'{text} | {" ".join(acting.split())[:160]}')
            return kit.deny(text + advice) if choice == 'deny' else kit.ask(text + advice)
        last = kit.state.get('told', 0)
        if asks or writes or kit.now - last >= float(kit.cfg.get('remind_seconds', 600)):
            kit.state['told'] = kit.now
            return kit.context(text + advice)
        return None
    return kit.context(text) if asks or writes else None


if __name__ == '__main__':
    sys.exit(hookkit.main('disk-floors', handle))
