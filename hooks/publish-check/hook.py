#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""publish-check: the publish check runs before anything of ours goes public.

Before a shell command that pushes: our commits that no remote has yet are checked.
Before a shell command that publishes text (an issue, a pull request, a comment, a release, a mail): the text in the
command and the files it sends are checked.
A hard finding (location data, another person's email address, a name that is never published, a secret) asks the
person; style notes come back as context only. README.md beside this file has the configuration and the reasons.
"""
import os
import re
import shlex
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, HERE)
import hookkit  # noqa: E402
import publish_check as pc  # noqa: E402

GH_TEXT = {('issue', 'create'), ('issue', 'comment'), ('issue', 'edit'), ('pr', 'create'), ('pr', 'comment'),
           ('pr', 'review'), ('pr', 'edit'), ('release', 'create'), ('release', 'edit'), ('release', 'upload')}
WRITE_METHODS = {'POST', 'PATCH', 'PUT'}
TEXT_PUBLISH = re.compile(r'gh\s+(issue|pr)\s+(create|comment|review|edit)|gh\s+release\s+(create|edit|upload)|git\s+send-email', re.I)
TEXT_PUSH = re.compile(r'\bgit\b[^|;&\n]*\bpush\b')


def publishes(words, mail):
    """'text' for a command that publishes text, 'mail' for one that mails it, None otherwise."""
    name = os.path.basename(words[0])
    if name == 'gh' and len(words) > 2:
        if (words[1], words[2]) in GH_TEXT:
            return 'text'
        if words[1] == 'api':
            method = [w.upper() for i, w in enumerate(words) if i and words[i - 1] in ('-X', '--method')]
            method += [w.split('=', 1)[1].upper() for w in words if w.startswith('--method=')]
            if set(method) & WRITE_METHODS or any(w.startswith('body=') for w in words):
                return 'text'
    if hookkit.git_subcommand(words)[0] == 'send-email' or any(r.search(' '.join(words[:6])) for r in mail):
        return 'mail'
    return None


def files_in(words, cwd):
    """The files a publishing command sends: the ones its options name, and words that are text or media files."""
    out = []
    for i, word in enumerate(words):
        candidate = None
        if word in ('--body-file', '-F', '--file', '--notes-file') and i + 1 < len(words):
            candidate = words[i + 1]
        elif '@' in word and word.split('@', 1)[0].endswith(('body', 'body=')):
            candidate = word.split('@', 1)[1]
        elif re.search(r'\.(md|txt|eml|patch|html)$', word, re.I) or word.lower().endswith(pc.MEDIA):
            candidate = word
        if candidate:
            path = os.path.expanduser(candidate if os.path.isabs(candidate) else os.path.join(cwd, candidate))
            if os.path.isfile(path) and os.path.getsize(path) < 50_000_000 and path not in out:
                out.append(path)
    return out


def check_push(cfg, words, cwd, rep):
    repo = hookkit.git_folder(words, cwd)
    rest = hookkit.git_subcommand(words)[1]
    places = [w for w in rest if not w.startswith('-')]
    remote = places[0] if places else 'origin'
    refs = [p.lstrip('+').split(':', 1)[0] for p in places[1:]]
    if '--all' in rest or '--mirror' in rest:
        refs = ['--branches']
    if not os.path.isdir(repo):
        return
    try:
        url = pc.git(repo, 'remote', 'get-url', remote).strip()
    except RuntimeError:
        url = remote
    revs = []
    for ref in [r for r in refs if r]:
        try:
            pc.git(repo, 'rev-parse', '--verify', '--quiet', ref + '^{commit}')
            revs.append(ref)
        except RuntimeError:
            if ref == '--branches':
                revs.append(ref)
    rep.extend(pc.check_repo(cfg, repo, revs or ['HEAD'], url))


def handle(event, kit):
    if event.kind != 'before-tool' or event.tool != 'shell':
        return None
    cfg = pc.Config(kit.cfg)
    mail_rx = [re.compile(r) for r in kit.cfg.get('mail_commands') or []]
    extra = [re.compile(r, re.I | re.S) for r in kit.cfg.get('publish_commands') or []]
    acting = event.acting_command()
    commands = event.commands()
    cwd = event.working_folder()
    rep = pc.Report()
    kinds, files = set(), []
    if commands is None:  # not readable as shell: judge the text
        if TEXT_PUSH.search(acting):
            check_push(cfg, ['git', 'push'], cwd, rep)
        if TEXT_PUBLISH.search(acting):
            kinds.add('mail' if 'send-email' in acting else 'text')
        try:
            files = files_in(shlex.split(acting), cwd)
        except ValueError:
            files = files_in(acting.split(), cwd)
    else:
        for words in commands:
            if hookkit.git_subcommand(words)[0] == 'push':
                check_push(cfg, words, cwd, rep)
            kind = publishes(words, mail_rx)
            if kind:
                kinds.add(kind)
                files += [f for f in files_in(words, cwd) if f not in files]
    if any(r.search(acting) for r in extra):
        kinds.add('text')
        if commands:
            for words in commands:
                files += [f for f in files_in(words, cwd) if f not in files]
    if kinds and not cfg.private_remote.search(acting):
        for n, line in enumerate(event.command.splitlines(), 1):
            sub = pc.Report()
            pc.check_line(cfg, sub, f'command line {n}', line, prose=True)
            if 'mail' in kinds:  # a mail names the people it goes to
                sub.hard = [h for h in sub.hard if 'email address' not in h]
                sub.soft = [s for s in sub.soft if 'email address' not in s]
            rep.extend(sub)
        if files:
            rep.extend(pc.check_files(cfg, files))
    hard = list(dict.fromkeys(rep.hard))
    soft = list(dict.fromkeys(rep.soft))
    if hard:
        text = ('Publish check: this would put into public something that must not go there (location data, another '
                "person's email address, a name that is never published, or a secret). Fix it first, or let the "
                'person decide.\n- ' + '\n- '.join(hard[:8]))
        if soft:
            text += '\nStyle notes:\n- ' + '\n- '.join(soft[:6])
        kit.log('findings.log', ' | '.join(hard[:8]))
        return kit.deny(text) if kit.cfg.get('on_hard_finding', 'ask') == 'deny' else kit.ask(text)
    if soft:
        return kit.context('Publish check, style notes (our own text: fix; text for another project: follow that '
                           'project\'s style):\n- ' + '\n- '.join(soft[:10]))
    return None


if __name__ == '__main__':
    sys.exit(hookkit.main('publish-check', handle))
