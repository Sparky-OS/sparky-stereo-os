#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""install.py: set a workspace up for the hooks, and write their wiring for a tool.

  install.py init WORKSPACE [--scratch DIR]    make the default folders, and each hook's configuration from its example
  install.py check WORKSPACE                   read every configuration and say what each hook will enforce
  install.py wire TOOL WORKSPACE [--write FILE] [--only HOOK,...] [--on-failure block]
                                               print the wiring for claude or codex; --write merges it into FILE
  install.py unwire FILE                       take this folder's hooks out of a settings file
  install.py git REPOSITORY WORKSPACE          point a repository's git hooks at publish-check (prints the commands)

Nothing is written outside WORKSPACE unless --write or unwire names the file, and an existing file is never replaced
without a unique copy beside it (FILE.before-hooks-DATE-UNIQUE). init never overwrites a file that exists.
"""
import argparse
import json
import os
import shlex
import shutil
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HOOKS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HOOKS, 'lib'))
import hookkit  # noqa: E402

PLACEHOLDER_WORKSPACE = '/path/to/your/workspace'
PLACEHOLDER_SCRATCH = '/path/to/your/scratch'
STARTERS = {
    'memory/MEMORY.md': '# Memory index\n\nOne fact per file in this folder, one line per file here.\n'
                        'Write each line so a search finds it: `- [Title](file.md): the words someone would look for`.\n',
    'partners/HOUSE-RULES.md': '# House rules\n\nThe rules every partner reads before work, person or model.\n'
                               'Start from the public skills (sparky-stereo, ai-partners) and add what this workspace needs.\n',
    'private/README.md': '# Private record\n\nDrafts, the ledger of what was sent and the hooks\' own configuration.\n'
                         'Nothing here goes into a repository that has a remote.\n',
    'private/ledger.md': '# Ledger\n\nWhat was sent, to whom, when, and what is owed after it.\n',
}
FOLDERS = ['memory', 'repos', 'partners/queue', 'private/drafts', 'private/hooks', 'state/hooks']


def hook_names():
    return sorted(n for n in os.listdir(HOOKS) if os.path.isfile(os.path.join(HOOKS, n, 'hook.py')))


def config_path(workspace, name):
    return os.path.join(workspace, 'private', 'hooks', name + '.json')


def init_workspace(workspace, scratch=None, say=print):
    """The default layout under workspace, and each hook's configuration from its example. Returns what was made."""
    workspace = os.path.abspath(os.path.expanduser(workspace))
    made = []
    for folder in FOLDERS:
        path = os.path.join(workspace, folder)
        if not os.path.isdir(path):
            os.makedirs(path)
            made.append(path)
    for rel, text in STARTERS.items():
        path = os.path.join(workspace, rel)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            made.append(path)
    os.chmod(os.path.join(workspace, 'private'), 0o700)
    checkout_skills = os.path.join(os.path.dirname(HOOKS), 'skills')
    default_skills = os.path.join(workspace, hookkit.LAYOUT['skills'])
    for name in hook_names():
        target = config_path(workspace, name)
        if os.path.exists(target):
            say(f'kept   {target}')
            continue
        with open(os.path.join(HOOKS, name, 'config.example.json'), encoding='utf-8') as f:
            # Placeholders occur inside JSON strings, including disk-floor keys.
            text = f.read().replace(PLACEHOLDER_WORKSPACE, json.dumps(workspace)[1:-1])
        if scratch:
            text = text.replace(PLACEHOLDER_SCRATCH, json.dumps(os.path.abspath(os.path.expanduser(scratch)))[1:-1])
        cfg = json.loads(text)
        floors = cfg.get('floors_gib')
        if isinstance(floors, dict):
            cfg['floors_gib'] = {k: v for k, v in floors.items() if not k.startswith('/path/to/your/')}
        if 'skills' in (cfg.get('paths') or {}) and not os.path.isdir(default_skills) and os.path.isdir(checkout_skills):
            cfg['paths']['skills'] = checkout_skills  # this checkout is not under WORKSPACE/repos: name where it is
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
            f.write('\n')
        os.chmod(target, 0o600)
        made.append(target)
        say(f'wrote  {target}')
    return made


def load(workspace, name):
    return hookkit.load_config(config_path(workspace, name))


def check_workspace(workspace, say=print):
    """Every hook's configuration read as the hook reads it, and the files it names looked for. Returns problems."""
    workspace = os.path.abspath(os.path.expanduser(workspace))
    problems = []
    for name in hook_names():
        try:
            cfg = load(workspace, name)
            kit = hookkit.Kit(name, cfg, config_path(workspace, name))
        except hookkit.HookError as e:
            problems.append(f'{name}: {e}')
            say(f'{name}: NOT USABLE: {e}')
            continue
        notes = []
        for key in (cfg.get('paths') or {}):
            if key not in ('state',) and not os.path.exists(kit.path(key)):
                notes.append(f'"{key}" does not exist: {kit.path(key)}')
        memory = kit.path('memory')
        for core in cfg.get('core') or []:
            if not os.path.exists(os.path.join(memory, core)):
                notes.append(f'core file not found: {os.path.join(memory, core)}')
        for rel in cfg.get('always_read') or []:
            if not os.path.exists(kit.resolve(rel)):
                notes.append(f'always_read file not found: {kit.resolve(rel)}')
        for floor in cfg.get('floors_gib') or {}:
            if not os.path.exists(floor):
                notes.append(f'floor path does not exist: {floor}')
        state = 'on' if cfg.get('enabled', True) else 'OFF ("enabled": false)'
        switches = ', '.join(f'{k} {"on" if v else "off"}' for k, v in sorted((cfg.get('on') or {}).items()))
        say(f'{name}: {state}{"; " + switches if switches else ""}')
        for note in notes:
            say(f'    {note}')
        problems += [f'{name}: {n}' for n in notes]
    return problems


def command_for(name, workspace, tool):
    parts = ['python3', os.path.join(HOOKS, name, 'hook.py'), '--config', config_path(workspace, name)]
    if tool != 'claude':
        parts += ['--dialect', tool]
    return ' '.join(shlex.quote(p) for p in parts)


def wiring(tool, workspace, only=None, on_failure=None):
    """The tool's hooks block: every hook's wiring.json merged, one matcher group per event and matcher."""
    workspace = os.path.abspath(os.path.expanduser(workspace))
    events = {}
    for name in hook_names():
        if only and name not in only:
            continue
        with open(os.path.join(HOOKS, name, 'wiring.json'), encoding='utf-8') as f:
            entries = json.load(f).get(tool)
        if entries is None:
            continue
        for entry in entries:
            matcher = entry.get('matcher')
            if 'matcher_from_config' in entry:
                values = load(workspace, name).get(entry['matcher_from_config']) or []
                if not values:
                    continue
                matcher = '|'.join(values)
            handler = {'type': 'command', 'command': command_for(name, workspace, tool), 'timeout': entry.get('timeout', 20)}
            if on_failure:
                handler['onFailure'] = on_failure
            groups = events.setdefault(entry['event'], [])
            for group in groups:
                if group.get('matcher') == matcher:
                    group['hooks'].append(handler)
                    break
            else:
                group = {'hooks': [handler]}
                if matcher is not None:
                    group = {'matcher': matcher, 'hooks': [handler]}
                groups.append(group)
    return {'hooks': events}


def is_ours(handler):
    return isinstance(handler, dict) and (HOOKS + os.sep) in str(handler.get('command', ''))


def strip_ours(settings):
    """Remove this folder's handlers from a settings object; returns how many went."""
    removed = 0
    hooks = settings.get('hooks')
    if not isinstance(hooks, dict):
        return 0
    for event in list(hooks):
        groups = []
        for group in hooks[event]:
            kept = [h for h in group.get('hooks', []) if not is_ours(h)]
            removed += len(group.get('hooks', [])) - len(kept)
            if kept:
                groups.append({**group, 'hooks': kept})
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    if not hooks:
        del settings['hooks']
    return removed


def read_settings(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f'{path} is not a JSON object')
    return data


def write_settings(path, settings, say=print):
    if os.path.exists(path):
        prefix = os.path.basename(path) + '.before-hooks-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-'
        with tempfile.NamedTemporaryFile(prefix=prefix, dir=os.path.dirname(os.path.abspath(path)), delete=False) as backup:
            copy = backup.name
        shutil.copy2(path, copy)
        say(f'copy   {copy}')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f'{path}.{os.getpid()}.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')
    os.replace(tmp, path)
    say(f'wrote  {path}')


def merge_into(path, block, say=print):
    """Put block's hooks into the settings file at path, replacing this folder's earlier entries and no others."""
    settings = read_settings(path)
    strip_ours(settings)
    hooks = settings.setdefault('hooks', {})
    for event, groups in block['hooks'].items():
        hooks.setdefault(event, []).extend(groups)
    write_settings(path, settings, say)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Set a workspace up for the hooks, and write their wiring for a tool.')
    sub = ap.add_subparsers(dest='action', required=True)
    p = sub.add_parser('init', help='make the default folders and each hook\'s configuration')
    p.add_argument('workspace')
    p.add_argument('--scratch', help='a folder for builds, given its own disk floor')
    p = sub.add_parser('check', help='read every configuration and say what each hook will enforce')
    p.add_argument('workspace')
    p = sub.add_parser('wire', help='print or write the wiring for a tool')
    p.add_argument('tool', choices=sorted(hookkit.DIALECTS))
    p.add_argument('workspace')
    p.add_argument('--write', metavar='FILE', help='merge the wiring into this settings file (a copy is kept beside it)')
    p.add_argument('--only', help='comma-separated hook names; default: every hook')
    p.add_argument('--on-failure', choices=['block', 'continue'],
                   help='what the tool does when a hook cannot start or times out (Claude Code\'s onFailure); default: the tool\'s own')
    p = sub.add_parser('unwire', help='take this folder\'s hooks out of a settings file')
    p.add_argument('file')
    p = sub.add_parser('git', help='print the commands that point a repository\'s git hooks at publish-check')
    p.add_argument('repository')
    p.add_argument('workspace')
    a = ap.parse_args(argv)
    try:
        if a.action == 'init':
            init_workspace(a.workspace, a.scratch)
            print('Next: put your own values into the files under private/hooks (the lists, the names, the floors), '
                  f'then: install.py check {a.workspace}')
        elif a.action == 'check':
            problems = check_workspace(a.workspace)
            if problems:
                print(f'{len(problems)} thing(s) to fix before the hooks do their work.')
                return 1
            print('Every configuration reads, and every file it names exists.')
        elif a.action == 'wire':
            only = set(a.only.split(',')) if a.only else None
            unknown = (only or set()) - set(hook_names())
            if unknown:
                sys.exit(f'install.py: no such hook: {", ".join(sorted(unknown))} (there are: {", ".join(hook_names())})')
            for name in hook_names():
                if not only or name in only:
                    load(a.workspace, name)  # a missing configuration is said now, not at the first event
            block = wiring(a.tool, a.workspace, only, a.on_failure)
            if a.write:
                merge_into(a.write, block)
            else:
                print(json.dumps(block, indent=2))
        elif a.action == 'unwire':
            settings = read_settings(a.file)
            removed = strip_ours(settings)
            if removed:
                write_settings(a.file, settings)
            print(f'{removed} handler(s) of {HOOKS} removed from {a.file}')
        elif a.action == 'git':
            repo = os.path.abspath(os.path.expanduser(a.repository))
            cfg = config_path(os.path.abspath(os.path.expanduser(a.workspace)), 'publish-check')
            print(f'git -C {shlex.quote(repo)} config core.hooksPath {shlex.quote(os.path.join(HOOKS, "publish-check", "git"))}')
            print(f'git -C {shlex.quote(repo)} config sparky.publishCheckConfig {shlex.quote(cfg)}')
            print('# to undo: git -C REPOSITORY config --unset core.hooksPath; git -C REPOSITORY config --unset sparky.publishCheckConfig')
    except (hookkit.HookError, OSError, ValueError) as e:
        sys.exit(f'install.py: {e}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
