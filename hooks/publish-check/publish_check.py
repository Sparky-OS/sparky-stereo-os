#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""publish_check: look at what is about to go public, before it goes.

Hard findings, fixed before publishing:
  location data in photos and videos; another person's email address in our text;
  a name the configuration says is never published; a secret (token, key, password literal).
Style notes, for text written in the house voice (text for another project follows that project's style):
  a dash in the middle of a sentence; a phrase the configuration lists; hard-wrapped Markdown.

Usage:
  publish_check.py --config FILE [--repo DIR] [REV...]  commits about to be pushed: by default the ones on HEAD
                                                        that no remote has; only our own commits
  publish_check.py --config FILE --files FILE...        drafts, mails (.eml), pictures, videos
  publish_check.py --config FILE --text                 text on stdin
  publish_check.py --config FILE --audit N [--repo DIR] our last N commits, pushed or not
Without --config the file named by SPARKY_PUBLISH_CHECK_CONFIG is read.
Exit status: 0 clean or style notes only, 1 hard findings, 2 usage or setup error.
The names, the identities and the allowed addresses live in the configuration file, never in this script;
config.example.json beside it shows every key.
"""
import argparse
import email
import email.policy
import json
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

MEDIA = ('.jpg', '.jpeg', '.mpo', '.jps', '.heic', '.heif', '.avif', '.png', '.pns', '.webp',
         '.tif', '.tiff', '.dng', '.mp4', '.mov', '.m4v', '.3gp', '.mkv', '.webm')
PROSE = ('.md', '.markdown', '.txt', '.rst', '.adoc', '.html', '.htm', '.eml')
WRAPPED = ('.md', '.markdown')
FILE_TLDS = {'png', 'jpg', 'jpeg', 'svg', 'gif', 'webp', 'mpo', 'mp4', 'mov', 'js', 'css',
             'py', 'sh', 'md', 'txt', 'json', 'xml', 'qml', 'cpp', 'h', 'so', 'deb', 'zip',
             'service', 'socket', 'target', 'mount', 'timer', 'path', 'slice', 'scope', 'device', 'swap'}
LOG_NAME = re.compile(r'(?i)(dmesg|journal|\.log$|-log\.|/logs?/)')
SECRETS = [
    (re.compile(r'\bgh[pousr]_[A-Za-z0-9]{36,}'), 'a GitHub token'),
    (re.compile(r'\bgithub_pat_[A-Za-z0-9_]{40,}'), 'a GitHub token'),
    (re.compile(r'\bglpat-[A-Za-z0-9_-]{20,}'), 'a GitLab token'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'an AWS key'),
    (re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'), 'a Google API key'),
    (re.compile(r'\bxox[abposr]-[A-Za-z0-9-]{10,}'), 'a Slack token'),
    (re.compile(r'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}'), 'an API key'),
    (re.compile(r'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----'), 'a private key'),
    (re.compile(r'(?i)\b(?:pass(?:word|wd)?|secret|api[_-]?key|token)\b\s*[:=]\s*[\'"][^\'"\s]{8,}[\'"]'),
     'a password or key written as a literal'),
]
EMAIL = re.compile(r'(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b')
TRAILER = re.compile(r'^\s*(?:[A-Z][A-Za-z-]*-by|Cc|Co-Authored-By|Reported-by|Suggested-by|Link):', re.I)
CREDIT_LINE = re.compile(r'(?i)copyright|spdx-filecopyrighttext|\(c\)|\u00a9|author')
DASH = re.compile(r'[\w"\')\]*_`][ \t]*\u2014[ \t]*[\w"\'(\[*_`]|[\w"\')\]*_`][ \t]+\u2013[ \t]+[\w"\'(\[*_`]')
RANGE = re.compile(r'\d[ \t]*\u2013[ \t]*\d')
GPS_TAGS = ['-GPSLatitude', '-GPSLongitude', '-GPSPosition', '-GPSCoordinates',
            '-UserData:GPSCoordinates', '-Keys:GPSCoordinates', '-XMP:GPSLatitude']
RESERVED_DOMAINS = re.compile(r'(?i)(?:^|[@.])(?:example\.(?:org|com|net)|[\w-]+\.(?:example|invalid|test))$')


class ConfigError(Exception):
    """The configuration cannot be used, and the message says why."""


class Config:
    """The lists the check works from. Every one comes from the configuration file."""

    def __init__(self, source):
        if isinstance(source, dict):
            c, where = source, 'the configuration'
        else:
            where = str(source)
            try:
                with open(source, encoding='utf-8') as f:
                    c = json.load(f)
            except OSError as e:
                raise ConfigError(f'cannot read {where}: {e.strerror}') from e
            except ValueError as e:
                raise ConfigError(f'{where} is not valid JSON: {e}') from e
        try:
            self.ours = {e.lower() for e in c.get('our_identities') or []}
            self.allowed = {e.lower() for e in c.get('allowed_emails') or []} | self.ours
            self.allowed_re = [re.compile(r, re.I) for r in c.get('allowed_email_regex') or []]
            self.never = [(re.compile(n['regex'], re.I), n['why']) for n in c.get('never_name') or []]
            self.private_remote = re.compile(c.get('private_remotes_regex') or r'(?!x)x', re.I)
            style = c.get('style') or {}
            self.phrases = [(re.compile(p['regex'], re.I), p['say']) for p in style.get('phrases') or []]
        except (KeyError, TypeError, re.error) as e:
            raise ConfigError(f'{where}: a list is not in the shape config.example.json shows ({type(e).__name__}: {e})') from e
        self.dash = style.get('mid_sentence_dash', True)
        self.wrapped = style.get('hard_wrapped_markdown', True)
        checks = c.get('checks') or {}
        self.check_never = checks.get('never_name', True)
        self.check_secrets = checks.get('secrets', True)
        self.check_emails = checks.get('emails', True)
        self.check_location = checks.get('location_data', True)
        self.check_style = checks.get('style', True)

    def email_ok(self, addr):
        a = addr.lower()
        if a.rsplit('.', 1)[-1] in FILE_TLDS or RESERVED_DOMAINS.search(a.split('@', 1)[1]):
            return True  # a file name with an @ in it, or an address of the domains reserved for examples (RFC 2606)
        return a in self.allowed or any(r.search(a) for r in self.allowed_re)


class Report:
    def __init__(self):
        self.hard = []
        self.soft = []

    def add(self, hard, where, what):
        (self.hard if hard else self.soft).append(f'{where}: {what}')

    def extend(self, other):
        self.hard += other.hard
        self.soft += other.soft


def clip(s, n=110):
    s = s.strip()
    return s if len(s) <= n else s[:n] + '...'


def message_id_or_url(line, start, end, addr):
    left = line.rfind(' ', 0, start) + 1
    right = line.find(' ', end)
    token = line[left:right if right >= 0 else len(line)]
    local = addr.split('@', 1)[0]
    return ('://' in token or token[:start - left].endswith('/')
            or re.search(r'[0-9a-f]{12,}', local) is not None or re.search(r'(?i)message-id', line) is not None)


def dash_issue(line):
    text = RANGE.sub('', line)
    hits = list(DASH.finditer(text))
    lm = re.match(r'\s*([-*+]|\d+[.)])\s+', text)
    if hits and lm:
        p = re.sub(r'`[^`]*`', '`x`', re.sub(r'\]\([^)]*\)', ']', text[lm.end():hits[0].start() + 1])).strip()
        if p and not re.search(r'[.!?;:][*_)"\'\]]*\s|[.!?][*_)"\'\]]*$', p) and (
                (p[0] in '*_[`' and len(p) <= 200) or len(p.split()) <= 6):
            hits = hits[1:]  # a list item's first dash separates a name from its description
    return bool(hits)


def check_line(cfg, rep, where, line, prose, code=False):
    if cfg.check_never:
        for rx, why in cfg.never:
            if rx.search(line):
                rep.add(True, where, f'names {why}: "{clip(line)}"')
    if cfg.check_secrets:
        for rx, why in SECRETS:
            if rx.search(line):
                rep.add(True, where, f'looks like {why}; remove it and rotate it if it was real')
    log = bool(LOG_NAME.search(where))
    if cfg.check_emails:
        for m in EMAIL.finditer(line):
            addr = m.group(0)
            if cfg.email_ok(addr) or message_id_or_url(line, m.start(), m.end(), addr):
                continue
            if re.match(r':[\w~./-]', line[m.end():]):
                continue  # user@host:path is the address of a remote, not of a person
            if TRAILER.search(line) or (code and CREDIT_LINE.search(line)):
                continue
            rep.add((prose or not code) and not log, where,
                    f"another person's email address {addr}: no third-party contacts in public")
    if prose and not log and cfg.check_style:
        if cfg.dash and dash_issue(line):
            rep.add(False, where, f'dash in the middle of a sentence: "{clip(line)}"')
        for rx, say in cfg.phrases:
            m = rx.search(line)
            if m and not re.search(r'\\?["\u201c\']' + re.escape(m.group(0)) + r'\\?["\u201d\']', line, re.I):
                rep.add(False, where, f'"{m.group(0)}": {say}')


def wrapped_lines(text):
    """Line numbers (1-based) that continue a paragraph line, that is, hard wraps."""
    out = set()
    fence = False
    prev = ''
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                start = i + 1
                break
    for i in range(start, len(lines)):
        line = lines[i]
        s = line.strip()
        if s.startswith('```') or s.startswith('~~~'):
            fence = not fence
            prev = ''
            continue
        if fence or not s:
            prev = ''
            continue
        block = re.match(r'([-*+]|\d+[.)])\s|#|\||<|>|\[[^\]]+\]:|!\[', s) or line.startswith('    ')
        if prev and not block:
            p = prev.rstrip('\n')
            hard_break = p.endswith('  ') or p.endswith('\\')
            ends = re.search(r'[.!?:;][)"\'*_`\]]*$', p.strip())
            if not hard_break and not ends and re.match(r'[a-z(]', s):
                out.add(i + 1)
        prev = line if not re.match(r'\||#|<', s) else ''
    return out


def is_patch_series(text):
    """A quilt series file: every line a patch name (with an optional -pN), a comment or blank."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    return bool(lines) and all(re.fullmatch(r'\S+\.(patch|diff)(\s+-p\d+)?', ln) for ln in lines)


def check_text(cfg, text, name, ext='.md'):
    rep = Report()
    if ext == '' and text.startswith('#!'):
        ext = '.sh'  # a file without an extension that starts with #! is a script, not prose
    prose = ext in PROSE or ext == ''
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if re.match(r'\s{0,3}(```|~~~)', line):
            fence = not fence
        code = fence or line.startswith('    ') and not re.match(r'\s*([-*+]|\d+[.)])\s', line)
        # a patch's context and removed lines are the other project's own text; what the patch adds stays strict
        if ext in ('.patch', '.diff') and (line.startswith(' ') or (line.startswith('-') and not line.startswith('---'))):
            code = True
        quoted = re.match(r'\s{0,3}>', line) is not None
        check_line(cfg, rep, f'{name}:{n}', line, prose and not code and not quoted, code=code)
    if cfg.check_style and cfg.wrapped and (ext in WRAPPED or (ext == '' and not is_patch_series(text))):
        for n in sorted(wrapped_lines(text))[:12]:
            rep.add(False, f'{name}:{n}', 'hard-wrapped line: one sentence per line, never wrapped')
    return rep


def check_eml(cfg, path):
    with open(path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)
    rep = check_text(cfg, str(msg.get('Subject', '')), f'{path} (subject)', '.txt')
    for part in msg.walk():
        if part.get_content_type() != 'text/plain':
            continue
        lines = [ln for ln in part.get_content().splitlines() if not ln.startswith('>') and not re.search(r'wrote:\s*$', ln)]
        rep.extend(check_text(cfg, '\n'.join(lines), path, '.txt'))
    return rep


def check_media(cfg, path, name):
    rep = Report()
    if not cfg.check_location:
        return rep
    try:
        r = subprocess.run(['exiftool', '-q', '-q', '-s', '-a', '-G1', *GPS_TAGS, path], capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        rep.add(True, name, 'location data NOT checked: exiftool is not installed (Debian: libimage-exiftool-perl); '
                            'install it, or switch "location_data" off under "checks" and say so')
        return rep
    except subprocess.TimeoutExpired:
        rep.add(True, name, 'location data NOT checked: exiftool did not answer in 60 s')
        return rep
    if r.returncode:
        rep.add(True, name, f'location data NOT checked: exiftool exited {r.returncode}; '
                'check that the file is readable and supported, then run the check again')
        return rep
    tags = [ln.split(':', 1)[0].strip() for ln in r.stdout.splitlines() if ln.strip()]
    if tags:
        rep.add(True, name, 'location data (' + ', '.join(sorted({t.split()[-1] for t in tags}))
                + '); strip it: exiftool -gps:all= -UserData:GPSCoordinates= -Keys:GPSCoordinates= FILE')
    return rep


def check_files(cfg, paths):
    rep = Report()
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        try:
            if ext in MEDIA:
                rep.extend(check_media(cfg, p, p))
            elif ext == '.eml':
                rep.extend(check_eml(cfg, p))
            else:
                with open(p, errors='replace') as f:
                    rep.extend(check_text(cfg, f.read(), p, ext))
        except OSError as e:
            rep.add(True, p, f'NOT checked: cannot be read ({e.strerror})')
    return rep


def git(repo, *args, binary=False):
    r = subprocess.run(['git', '-C', repo, *args], capture_output=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors='replace').strip())
    return r.stdout if binary else r.stdout.decode(errors='replace')


def added_lines(repo, commit, path):
    out = {}
    n = 0
    for line in git(repo, 'show', '-U0', '--format=', '--no-ext-diff', commit, '--', path).splitlines():
        m = re.match(r'@@ -\S+ \+(\d+)(?:,(\d+))? @@', line)
        if m:
            n = int(m.group(1))
            continue
        if line.startswith('+') and not line.startswith('+++'):
            out[n] = line[1:]
            n += 1
    return out


def check_commit(cfg, repo, c):
    rep = Report()
    short = c[:9]
    for line in git(repo, 'show', '-s', '--format=%B', c).splitlines():
        check_line(cfg, rep, f'commit {short} message', line, prose=False, code=False)
    changed = git(repo, 'diff-tree', '--root', '--no-commit-id', '-r', '--diff-filter=AM', '--name-only', c).splitlines()
    binaries = set()
    for line in git(repo, 'diff-tree', '--root', '--no-commit-id', '-r', '--diff-filter=AM', '--numstat', c).splitlines():
        parts = line.split('\t')
        if len(parts) == 3 and parts[0] == '-':
            binaries.add(parts[2])
    for path in changed:
        ext = os.path.splitext(path)[1].lower()
        where = f'commit {short} {path}'
        if ext in MEDIA:
            with tempfile.NamedTemporaryFile(suffix=ext) as tmp:
                tmp.write(git(repo, 'cat-file', 'blob', f'{c}:{path}', binary=True))
                tmp.flush()
                rep.extend(check_media(cfg, tmp.name, where))
            continue
        if path in binaries:
            continue
        prose = ext in PROSE
        added = added_lines(repo, c, path)
        for n, line in added.items():
            check_line(cfg, rep, f'{where}:{n}', line, prose, code=not prose)
        if cfg.check_style and cfg.wrapped and ext in WRAPPED and added:
            wraps = wrapped_lines(git(repo, 'show', f'{c}:{path}'))
            if len(wraps - set(added)) >= 2:
                continue  # the file is wrapped already: its own style wins
            for n in sorted(wraps & set(added))[:12]:
                rep.add(False, f'{where}:{n}', 'hard-wrapped line: one sentence per line, never wrapped')
    return rep


def commits_to_check(cfg, repo, revs, audit=0):
    revs = revs or ['HEAD']
    limit = ['--max-count=' + str(audit)] if audit else ['--max-count=400', '--not', '--remotes']
    lines = git(repo, 'log', '--no-merges', '--format=%H %ae', *revs, *limit).splitlines()
    return [ln.split()[0] for ln in lines if len(ln.split()) > 1 and ln.split()[1].lower() in cfg.ours]


def check_repo(cfg, repo, revs, remote_url='', audit=0):
    rep = Report()
    if remote_url and cfg.private_remote.search(remote_url):
        return rep
    for c in commits_to_check(cfg, repo, revs, audit):
        rep.extend(check_commit(cfg, repo, c))
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description='Check what is about to go public.')
    ap.add_argument('--config', default=os.environ.get('SPARKY_PUBLISH_CHECK_CONFIG'),
                    help='the configuration file (default: the one named by SPARKY_PUBLISH_CHECK_CONFIG)')
    ap.add_argument('--repo', default='.')
    ap.add_argument('--files', nargs='+')
    ap.add_argument('--text', action='store_true')
    ap.add_argument('--audit', type=int, default=0, metavar='N', help='check our last N commits, pushed or not')
    ap.add_argument('revs', nargs='*')
    a = ap.parse_args(argv)
    if not a.config:
        print('publish_check: no configuration: give --config FILE or set SPARKY_PUBLISH_CHECK_CONFIG '
              '(config.example.json beside this script shows every key)', file=sys.stderr)
        return 2
    try:
        cfg = Config(a.config)
        if a.files:
            rep = check_files(cfg, a.files)
        elif a.text:
            rep = check_text(cfg, sys.stdin.read(), 'stdin', '')
        else:
            if not cfg.ours:
                print('publish_check: "our_identities" is empty, so no commit counts as ours and none would be checked', file=sys.stderr)
                return 2
            try:
                url = git(a.repo, 'remote', 'get-url', 'origin').strip()
            except RuntimeError:
                url = ''
            rep = check_repo(cfg, a.repo, a.revs, url, a.audit)
    except (ConfigError, RuntimeError, OSError) as e:
        print(f'publish_check: {e}', file=sys.stderr)
        return 2
    for h in dict.fromkeys(rep.hard):
        print('STOP  ' + h)
    for s in dict.fromkeys(rep.soft):
        print('style ' + s)
    if not rep.hard and not rep.soft:
        print('publish-check: clean')
    return 1 if rep.hard else 0


if __name__ == '__main__':
    sys.exit(main())
