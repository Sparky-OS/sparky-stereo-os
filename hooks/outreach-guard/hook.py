#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""outreach-guard: nothing leaves for another project until the rules for it were read in this session.

After a read or a consult of the reference index: the time is noted.
Before a shell command that sends something to another project (a pull or merge request, a comment, an issue, a
review, a write to a forge, a mail, a push to a fork of someone else's project): refused until this session has,
within the window, read in full the files the configuration names and the contrib skill of the project the command
names, and has consulted the reference index. Then the command passes, with the filing checklist as context.
Commands on the workspace's own repositories pass. README.md beside this file has the configuration and the reasons.
"""
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import hookkit  # noqa: E402

GH_ACTS = {'create', 'comment', 'review', 'edit', 'close', 'reopen', 'merge'}
WRITE_METHODS = {'POST', 'PATCH', 'PUT', 'DELETE'}
GH_FIELDS = {'-f', '-F', '--field', '--raw-field', '--input'}
CURL_SENDS = {'-d', '--data', '--data-binary', '--data-raw', '--data-urlencode', '--json', '-T', '--upload-file', '-F', '--form'}
GITHUB = re.compile(r'github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?(?:[\s/\'"]|$)')
REPOS_NAMED = re.compile(r'(?:--repo|-R)[ =]+([\w.-]+)/([\w.-]+)|\brepos/([\w.-]+)/([\w.-]+)')
# only when a line cannot be read as shell: the same questions asked of its text
TEXT_GH = re.compile(r'\bgh\s+(?:pr|issue)\s+(?:create|comment|review|edit|close|reopen|merge)\b')
TEXT_PUSH = re.compile(r'\bgit\b[^|;&\n]*\bpush\b')


class Rules:
    def __init__(self, cfg):
        self.owners = {o.lower() for o in cfg.get('own_owners') or []}
        self.repos = {r.lower() for r in cfg.get('own_repos') or []}
        self.own_urls = [re.compile(r, re.I) for r in cfg.get('own_urls') or []]
        self.forges = [re.compile(r, re.I) for r in cfg.get('forges') or []]
        self.mail = [re.compile(r) for r in cfg.get('mail_commands') or []]
        self.fork_remotes = set(cfg.get('fork_remote_names') or [])
        self.resolve = cfg.get('resolve_remotes', True)

    def named_are_ours(self, text):
        """True when the command names repositories and every one belongs to the workspace's own accounts."""
        owners = [a or c for a, _, c, _ in REPOS_NAMED.findall(text)]
        return bool(owners) and all(o.lower() in self.owners for o in owners)

    def address_goes_out(self, url):
        """Why a push to this address reaches another project, or None."""
        if any(r.search(url) for r in self.own_urls):
            return None
        m = GITHUB.search(url + ' ')
        if m:
            if m.group(1).lower() in self.owners and m.group(2).lower() in self.repos:
                return None
            return 'a push to a fork of another project (it can update an open pull request)'
        if any(r.search(url) for r in self.forges):
            return "a push to another project's forge"
        return None

    def address_is_our_project(self, url):
        return bool(url) and self.address_goes_out(url) is None and (
            GITHUB.search(url + ' ') is not None or any(r.search(url) for r in self.own_urls))


def remote_url(folder, remote):
    try:
        r = subprocess.run(['git', '-C', folder, 'remote', 'get-url', '--push', remote], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ''
    return r.stdout.strip() if r.returncode == 0 else ''


def one_command(words, rules, cwd):
    """(why this simple command sends something to another project or None, the address it resolved)."""
    name = os.path.basename(words[0])
    text = ' '.join(words)
    if name == 'gh' and len(words) > 1:
        write = len(words) > 2 and words[1] in ('pr', 'issue') and words[2] in GH_ACTS
        if words[1] == 'api':
            method = [w.upper() for i, w in enumerate(words) if i and words[i - 1] in ('-X', '--method')]
            method += [w.split('=', 1)[1].upper() for w in words if w.startswith('--method=')]
            method += [w[2:].upper() for w in words if w.startswith('-X') and len(w) > 2]
            write = bool(set(method) & WRITE_METHODS) or bool(set(words) & GH_FIELDS)
        if not write or rules.named_are_ours(text):
            return None, ''
        if not REPOS_NAMED.search(text) and rules.resolve:
            url = remote_url(cwd, 'origin')  # gh acts on the repository of the folder it runs in
            if rules.address_is_our_project(url):
                return None, url
        return 'a pull request, issue, comment or forge write on a repository that is not ours', ''
    if name == 'curl':
        method = [w.upper() for i, w in enumerate(words) if i and words[i - 1] in ('-X', '--request')]
        method += [w[2:].upper() for w in words if w.startswith('-X') and len(w) > 2]
        sends = bool(set(method) & WRITE_METHODS) or bool(set(words) & CURL_SENDS) or any(w.startswith('--data') for w in words)
        if sends and any(r.search(text) for r in rules.forges):
            if rules.named_are_ours(text) or any(r.search(text) for r in rules.own_urls):
                return None, ''
            return "a write to another project's forge", ''
        return None, ''
    if any(r.search(' '.join(words[:6])) for r in rules.mail):
        return 'a mail', ''
    if name == 'reportbug' and '-o' not in words and not any(w.startswith('--output') for w in words):
        return 'a bug report by mail', ''  # with -o it only writes the report to a file
    sub, rest = hookkit.git_subcommand(words)
    if sub == 'push':
        places = hookkit.push_places(rest)
        remote = places[0] if places else 'origin'
        if '://' in remote or '@' in remote or GITHUB.search(remote + ' '):
            return rules.address_goes_out(remote), remote
        if rules.resolve:
            url = remote_url(hookkit.git_folder(words, cwd), remote)
            if url:
                return rules.address_goes_out(url), url
        if remote in rules.fork_remotes:
            return 'a push to a fork remote (it can update an open pull request)', ''
    return None, ''


def outward(event, rules):
    """(why the shell line sends something to another project or None, the text to search for a project's name)."""
    acting = event.acting_command()
    commands = event.commands()
    if commands is None:  # not readable as shell: ask the text, as a careful reader would
        if TEXT_GH.search(acting) and not rules.named_are_ours(acting):
            return 'a pull request, issue or comment on a repository that is not ours', acting
        if any(r.search(acting) for r in rules.mail):
            return 'a mail', acting
        if TEXT_PUSH.search(acting):
            why = rules.address_goes_out(acting)
            if not why and re.search(r'\bpush\b[^|;&\n]*\b(?:' + '|'.join(map(re.escape, rules.fork_remotes)) + r')\b', acting) and rules.fork_remotes:
                why = 'a push to a fork remote (it can update an open pull request)'
            return why, acting
        return None, acting
    cwd = event.working_folder()
    for words in commands:
        why, address = one_command(words, rules, cwd)
        if why:
            return why, acting + ' ' + address
    return None, acting


def needed(text, kit):
    """The files this command needs read: the standing ones, and the contrib skill of each project it names."""
    need = [kit.resolve(p) for p in kit.cfg.get('always_read') or []]
    skills = kit.path('skills')
    for project in kit.cfg.get('projects') or []:
        if re.search(project['pattern'], text, re.I):
            need.append(os.path.join(skills, project['skill'], 'SKILL.md'))
    out = []
    for path in need:
        if path in out:
            continue
        if os.path.exists(path):
            out.append(path)
        elif path not in kit.state.setdefault('missing_said', []):
            kit.state['missing_said'].append(path)
            kit.log('errors.log', f'a file the configuration asks to be read does not exist, so it is not demanded: {path}')
    return out


def handle(event, kit):
    state = kit.state
    if event.kind == 'after-tool':
        watched = [os.path.realpath(kit.path('memory')), os.path.realpath(kit.path('skills'))]
        listed = {os.path.realpath(kit.resolve(p)) for p in kit.cfg.get('always_read') or []}
        for path in event.reads(kit.cfg.get('shell_reads')):
            real = os.path.realpath(path)
            if real in listed or any(real.startswith(w + os.sep) for w in watched):
                state.setdefault('read', {})[real] = kit.now
        if event.tool_name in (kit.cfg.get('consult_tools') or []):
            state['consult'] = kit.now
        return None
    if event.kind != 'before-tool' or event.tool != 'shell':
        return None
    why, text = outward(event, Rules(kit.cfg))
    if not why:
        return None
    window = float(kit.cfg.get('window_seconds', 14400))
    read = state.get('read', {})
    missing = [p for p in needed(text, kit) if kit.now - read.get(os.path.realpath(p), 0) > window]
    tools = kit.cfg.get('consult_tools') or []
    no_consult = bool(kit.cfg.get('require_consult', True)) and bool(tools) and kit.now - state.get('consult', 0) > window
    short = ' '.join(event.acting_command().split())[:200]
    if missing or no_consult:
        lines = [f'[Outreach guard: this command is {why}. It is refused until this session has, within the last {window / 3600:g} hours:]']
        if missing:
            lines.append('Read in full, with the file-reading tool:')
            lines += [f'- {p}' for p in missing]
        if no_consult:
            lines.append(f'Consulted the reference index for this subject ({", ".join(tools)}); an empty answer is recorded as it is.')
        hint = kit.lookup_hint('PROJECT SUBJECT')
        if hint:
            lines.append(f'Search the memory by content for the project and the subject too ({hint}).')
        lines.append('Then send the same command again.')
        kit.log('refused.log', f'{why} | {short}')
        return kit.deny('\n'.join(lines))
    kit.log('passed.log', f'{why} | {short}')
    checklist = kit.cfg.get('checklist') or []
    if not checklist:
        return None
    return kit.context('[Outreach: the rules were read. Before this goes out, each of these holds, or it stops here.]\n'
                       + '\n'.join(f'- {line}' for line in checklist))


if __name__ == '__main__':
    sys.exit(hookkit.main('outreach-guard', handle))
