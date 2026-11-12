#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""stereo-contract-guard: a tool call that would put a broken stereo contract into a lane brief, a text for another
project or a pushed branch is stopped and put to the person.

The contract: programs read every stereo input and hand the desktop one format, full side by side, left eye first,
declared once. Output formats belong to the desktop's outputs only (Stereo KWin, KScreen, gamescope).
In a program, anaglyph is input only: detect an anaglyph picture, rebuild the pair.

Checks, each with its switch under "checks" in the configuration:
  program_output_modes  a sentence, or an added code line, where a program is given an output format of its own
  declaration           a declaration other than full side by side
  lane_notes_in_push    lane notes (reports, briefs, evidence) in the commits about to be pushed
  keeping_own_modes     a sentence where a program's own output modes stay beside the declared pair
It answers "ask" with each finding, its rule and its fix, and never refuses anything else.
README.md beside this file has the configuration and the reasons.
"""
import os
import re
import shlex
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import hookkit  # noqa: E402

ALLOW = (r'kwin|kscreen|gamescope|compositor|the desktop|desktop\'s|output filter|outputs\b|virtual|'
         r'\binput\b|detect|convert|rebuild|de-anaglyph|anaglyph pictures?|anaglyphs\b|input only|from (an )?anaglyph|anaglyph[ -]to[ -]|'
         r'\bnever\b|\bno anaglyph|\bnot\b|without|wiki|glasses|icon|fox|logo')
OUTPUT_WORDS = re.compile(r'\b(view|preview|mode|modes|option|toggle|button|menu|switch\w*|profile|tool|output)\b', re.I)
DECLARE_BAD = re.compile(r'declar\w*[^.]{0,80}(half|top[ -]and[ -]bottom|right[ -]eye[ -]first|right first)', re.I)
DECLARE_ALLOW = re.compile(r'unpack|\binput\b|\bread|convert|\bfile|stream|\bnever\b|\bnot\b|withdrawn|instead', re.I)
KEEP_MODES = re.compile(
    r'\b(keep|keeps|kept|stay|stays|remain|remains|leave|leaves|left|available|reachable|offer|offers)\b[^.]{0,90}'
    r'\b(own|its|their|the other|other)\b[^.]{0,40}\b(output|stereo|3d|display|screen)?\s*modes?\b|'
    r'\bmodes?\b[^.]{0,60}\b(drawn|made|rendered) by [^.]{0,40}\bitself\b', re.I)
KEEP_ALLOW = re.compile(r'\b(go|goes|gone|removed|hidden|dropped|lose|loses|never|not|no longer)\b|kwin|kscreen|gamescope|the desktop', re.I)
CODE_BAD = re.compile(r'anaglyph[_ ]?(view|preview|mode|output|toggle)|View\s*>\s*Anaglyph|set_?anaglyph|anaglyph_?enabled', re.I)  # never in a program
LANE_PATHS = r'(^|/)(REPORT[^/]*\.md|next-prompt[^/]*|AGENTS\.md|BRIEF\.md|evidence/|round\d+/|ci-diagnosis/|package-proof/)'
GH_TEXT = {('issue', 'create'), ('issue', 'comment'), ('issue', 'edit'), ('pr', 'create'), ('pr', 'comment'), ('pr', 'review'), ('pr', 'edit')}
TEXT_PUBLISH = re.compile(r'gh\s+(issue|pr)\s+(create|comment|review|edit)|git\s+send-email', re.I)
TEXT_PUSH = re.compile(r'\bgit\b[^|;&\n]*\bpush\b')
A_RULE = ('Not compliant: a program never makes anaglyph or any screen format; it declares full side by side and the '
          'desktop\'s outputs (Stereo KWin, KScreen, gamescope) make anaglyph. Allowed: anaglyph as input (detect it, rebuild '
          'the pair). Fix: drop the view, mode or option and declare the pair.')
B_RULE = ('Not compliant: the declaration is one value, full side by side, left eye first. Fix: unpack half, top and '
          'bottom or right-eye-first at the source, then declare full side by side.')
C_RULE = 'Not compliant: lane notes stay private, never in a source branch. Fix: git rm them on the branch and keep them in the lane folder.'
D_RULE = ('Not compliant: a program\'s own stereo output modes go in the edition\'s build; it hands the desktop full side '
          'by side, declared, and Stereo KWin makes every output for every screen. That is not removing functionality: '
          'there is no direct path to the screen. Fix: drop the program\'s modes, keep its declared side by side.')


WATCHED = ('anaglyph', 'declar', 'mode')  # a sentence without one of these is never judged


def sentences(text):
    for s in re.split(r'(?<=[.!?])\s+|\n', text):
        low = s.lower()
        if any(word in low for word in WATCHED):
            yield s.strip()


def text_findings(text, checks, allow):
    out = []
    for s in sentences(text):
        if checks.get('program_output_modes', True) and 'anaglyph' in s.lower() and OUTPUT_WORDS.search(s) and not allow.search(s):
            out.append(f'a program offering an output format: "{s[:160]}". {A_RULE}')
        if checks.get('keeping_own_modes', True) and KEEP_MODES.search(s) and not KEEP_ALLOW.search(s):
            out.append(f'a program keeping its own output modes: "{s[:160]}". {D_RULE}')
        if checks.get('declaration', True) and DECLARE_BAD.search(s) and not DECLARE_ALLOW.search(s):
            out.append(f'a declaration other than full side by side: "{s[:160]}". {B_RULE}')
    return out


def files_in(words, cwd):
    """The text files a publishing command sends, and the text files a script it runs opens."""
    paths = []
    for i, word in enumerate(words):
        candidate = None
        if word in ('--body-file', '-F', '--file') and i + 1 < len(words):
            candidate = words[i + 1]
        elif '@' in word and word.split('@', 1)[0].endswith(('body', 'body=')):
            candidate = word.split('@', 1)[1]
        elif re.search(r'\.(md|txt|py)$', word):
            candidate = word
        if not candidate:
            continue
        path = candidate if os.path.isabs(candidate) else os.path.join(cwd, candidate)
        if os.path.isfile(path) and os.path.getsize(path) < 400_000:
            paths.append(path)
            if path.endswith('.py'):
                with open(path, errors='ignore') as f:
                    source = f.read()
                for name in re.findall(r'open\(\s*[\'"]([^\'"]+\.(?:txt|md))[\'"]', source):
                    other = name if os.path.isabs(name) else os.path.join(os.path.dirname(path), name)
                    if os.path.isfile(other):
                        paths.append(other)
    return list(dict.fromkeys(paths))


def push_findings(repo, checks, display_stack, lane_paths):
    if not os.path.isdir(repo):
        return []

    def run(*args):
        return subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, timeout=20).stdout

    commits = run('rev-list', '--max-count=300', 'HEAD', '--not', '--remotes').split()
    if not commits:
        return []
    name = (run('remote', 'get-url', 'origin') + ' ' + repo).lower()
    display = any(d.lower() in name for d in display_stack)
    out, files = [], set()
    for c in commits:
        files.update(run('diff-tree', '--no-commit-id', '--name-only', '--diff-filter=AM', '-r', c).split('\n'))
        if not display and checks.get('program_output_modes', True):
            for line in run('show', '--format=', c).splitlines():
                if line.startswith('+') and not line.startswith('+++') and CODE_BAD.search(line):
                    out.append(f'output-mode code in commit {c[:9]}: {line.strip()[:140]}. Not compliant: output-mode code in a '
                               'program outside the display stack. Allowed: input code (detecting an anaglyph, rebuilding the '
                               'pair). Fix: remove the output mode; declare full side by side.')
                    break
    if checks.get('lane_notes_in_push', True):
        tip = set(run('ls-tree', '-r', '--name-only', 'HEAD').split('\n'))
        lane = sorted(f for f in files if f and lane_paths.search(f) and f in tip)
        if lane:
            out.append('lane notes in the pushed tip: ' + ', '.join(lane[:8]) + '. ' + C_RULE)
    return out


def handle(event, kit):
    if event.kind != 'before-tool':
        return None
    cfg = kit.cfg
    checks = cfg.get('checks') or {}
    allow = re.compile(ALLOW + ''.join('|' + re.escape(w) for w in cfg.get('allow_words') or []), re.I)
    watched = [kit.resolve(p) for p in cfg.get('watch_write_paths') or [kit.path('queue'), kit.path('drafts')]]
    findings, where = [], ''
    if event.tool in ('write', 'edit'):
        for path in event.paths:
            if any(os.path.normpath(path).startswith(w + os.sep) for w in watched):
                findings = text_findings(event.text, checks, allow)
                where = f'writing {path}'
                break
    elif event.tool == 'shell':
        acting = event.acting_command()
        commands = event.commands()
        cwd = event.working_folder()
        pushes, publishes, files = [], False, []
        if commands is None:
            if TEXT_PUSH.search(acting):
                pushes.append(cwd)
            publishes = bool(TEXT_PUBLISH.search(acting))
            try:
                files = files_in(shlex.split(acting), cwd)
            except ValueError:
                files = files_in(acting.split(), cwd)
        else:
            for words in commands:
                sub = hookkit.git_subcommand(words)[0]
                if sub == 'push':
                    pushes.append(hookkit.git_folder(words, cwd))
                if sub == 'send-email' or (os.path.basename(words[0]) == 'gh' and len(words) > 2 and (words[1], words[2]) in GH_TEXT) \
                        or (os.path.basename(words[0]) == 'gh' and len(words) > 1 and words[1] == 'api' and any(w.startswith('body=') for w in words)):
                    publishes = True
                    files += files_in(words, cwd)
        if any(re.search(r, acting, re.I | re.S) for r in cfg.get('publish_commands') or []):
            publishes = True
            for words in commands or []:
                files += files_in(words, cwd)
        display = cfg.get('display_stack') or []
        lane_paths = re.compile(cfg.get('lane_paths_regex') or LANE_PATHS)
        for repo in pushes:
            findings += push_findings(repo, checks, display, lane_paths)
            where = 'a git push'
        if publishes:
            text = event.command
            for path in dict.fromkeys(files):
                with open(path, errors='ignore') as f:
                    text += '\n' + f.read()
            findings += text_findings(text, checks, allow)
            where = where or 'publishing'
        elif any(w in event.command for w in watched) and re.search(
                r'>>?\s*\S*(?:' + '|'.join(map(re.escape, watched)) + r')|(?:' + '|'.join(map(re.escape, watched)) + r')\S*\s*<<', event.command):
            findings += text_findings(event.command, checks, allow)  # a brief or a draft written by the shell
            where = where or 'writing a lane brief or a draft'
    findings = list(dict.fromkeys(findings))
    if not findings:
        return None
    kit.log('findings.log', f'{where} | ' + ' | '.join(f[:120] for f in findings[:6]))
    text = (f'Stereo contract guard, {where}: programs hand the desktop full side by side, declared once; anaglyph is '
            'input only (detect, rebuild the pair); output modes belong to Stereo KWin, KScreen and gamescope. Findings:\n- '
            + '\n- '.join(findings[:6]))
    return kit.deny(text) if cfg.get('on_finding', 'ask') == 'deny' else kit.ask(text)


if __name__ == '__main__':
    sys.exit(hookkit.main('stereo-contract-guard', handle))
