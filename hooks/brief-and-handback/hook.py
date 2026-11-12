#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""brief-and-handback: a lane is not sent out blind, and its report does not come back without its proof of reading.

Before a dispatch: the brief the dispatch names must quote its design and name the skill to leave behind.
Before a brief is written: the memory files that hold its subject are shown, found by content.
Before a hand-back: the report must carry the sections the house asks for.
At session start, in the coordinator's session: the lanes that wait for a review are listed.
README.md beside this file has the configuration and the reasons.
"""
import os
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import design_lookup  # noqa: E402
import hookkit  # noqa: E402

BRIEF = r'(?:BRIEF[^/\s"\'`]*|AGENTS)\.md'
REPORT = r'REPORT\.md'
STOP = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'into', 'order', 'lane', 'review', 'study', 'fix', 'fixes',
        'new', 'make', 'makes', 'when', 'what', 'must', 'does', 'only', 'after', 'before', 'work', 'works', 'round'}
REMINDER = ('Lane dispatch: its brief quotes the design of every part it touches; its hand-back carries a Design check, '
            'read against the memory before it is accepted, and the Skill changes, reviewed and merged with the work.')


def under(path, folder):
    return os.path.normpath(path).startswith(os.path.normpath(folder) + os.sep)


def heading_rx(words):
    """A heading of these words, with or without a leading "The", the first word singular or plural."""
    first, *rest = words.split()
    return re.compile(r'^##+\s*(?:the\s+)?' + r'\s+'.join([re.escape(first) + 's?'] + [re.escape(w) for w in rest]) + r'\b.*$',
                      re.M | re.I)


def brief_problems(path, kit):
    cfg = kit.cfg.get('brief') or {}
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            text = f.read(400_000)
    except OSError as e:
        return [f'it cannot be read ({e.strerror})']
    problems = []
    for words in cfg.get('headings', ['Design', 'The skill to leave behind']):
        if not heading_rx(re.sub(r'^the\s+', '', words, flags=re.I)).search(text):
            problems.append(f'no "## {words}" section')
    design = heading_rx('Design').search(text)
    if design:
        rest = text[design.end():]
        nxt = re.search(r'^##\s', rest, re.M)
        section = rest[:nxt.start()] if nxt else rest
        if cfg.get('design_names_a_memory', True):
            try:
                stems = [n[:-3] for n in os.listdir(kit.path('memory')) if n.endswith('.md')]
            except OSError:
                stems = []
            index = os.path.basename(kit.path('memory_index'))[:-3]
            if not any(s in section for s in stems if s != index):
                problems.append('its Design section names no memory file (name the file each quoted line comes from)')
        if cfg.get('design_quotes', True) and '"' not in section and '“' not in section:
            problems.append('its Design section quotes nothing (put the governing words in quotes)')
    for phrase in cfg.get('must_say', ['Design check', 'Skill changes']):
        if phrase not in text:
            problems.append(f'it does not ask for "{phrase}" in the hand-back')
    return problems


def subject_words(path, content):
    slug = os.path.basename(os.path.dirname(path))
    words = [w for w in re.split(r'[-_]', slug) if len(w) >= 3 and not re.search(r'\d', w) and w.lower() not in STOP]
    title = re.search(r'^#\s+(.+)$', content or '', re.M)
    if not title and os.path.exists(path):
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                title = re.search(r'^#\s+(.+)$', f.read(20_000), re.M)
        except OSError:
            title = None
    if title:
        for w in re.findall(r'[A-Za-z][A-Za-z0-9+.-]{3,}', title.group(1)):
            if w.lower() not in STOP and not re.search(r'\d', w) and w not in words:
                words.append(w)
    return [re.escape(w) for w in words[:10]]


def handback_problems(text, kit):
    cfg = kit.cfg.get('handback') or {}
    problems = []
    first = text.lstrip().split('\n', 1)[0]
    if cfg.get('first_line') and not re.search(cfg['first_line'], first):
        problems.append(f'its first line is not a status line ({cfg["first_line"]})')
    for phrase in cfg.get('must_have', ['Design check', 'Corpus consulted', 'Skill changes']):
        if phrase.lower() not in text.lower():
            problems.append(f'no "{phrase}" section')
    return problems


def waiting_lanes(kit):
    cfg = kit.cfg.get('waiting_lanes') or {}
    queue = kit.path('queue')
    status = re.compile(cfg.get('status', r'^STATUS: (review|blocked)'))
    limit = float(cfg.get('max_age_days', 3)) * 86400
    found = []
    try:
        lanes = sorted(os.scandir(queue), key=lambda e: e.name)
    except OSError:
        return []
    for lane in lanes[:5000]:
        report = os.path.join(lane.path, 'REPORT.md')
        try:
            if time.time() - os.path.getmtime(report) > limit:
                continue
            with open(report, encoding='utf-8', errors='replace') as f:
                first = f.readline().strip()
        except OSError:
            continue
        if status.search(first):
            found.append(f'{lane.name} ({first[:60]})')
    return found[:int(cfg.get('max_listed', 12))]


def handle(event, kit):
    queue = kit.path('queue')
    brief_rx = re.compile(re.escape(queue) + r'/[^\s"\'`]+?/' + (kit.cfg.get('brief_pattern') or BRIEF))

    if event.kind == 'session-start':
        if event.agent or not kit.on('waiting_lanes'):
            return None
        lanes = waiting_lanes(kit)
        return kit.context('Lanes waiting for a review now: ' + '; '.join(lanes) + '.') if lanes else None

    if event.kind != 'before-tool':
        return None

    if event.tool == 'dispatch' and kit.on('dispatch'):
        problems = []
        for path in sorted(set(brief_rx.findall(event.text))):
            problems += [f'{path}: {p}' for p in brief_problems(path, kit)]
        if problems:
            kit.log('refused.log', 'dispatch | ' + '; '.join(problems))
            return kit.deny('Lane brief not ready: ' + '; '.join(problems) + '. Search the memory by content for the '
                            'subject, read what it names, quote the governing lines in the brief, name the skill the '
                            'lane leaves behind, then dispatch again.')
        return kit.context(kit.cfg.get('dispatch_reminder', REMINDER)) if kit.on('dispatch_reminder') else None

    if event.tool in ('write', 'edit'):
        report_rx = re.compile(re.escape(queue) + r'/[^\s"\'`]+?/' + (kit.cfg.get('report_pattern') or REPORT))
        for path in event.paths:
            if brief_rx.fullmatch(path) and kit.on('brief_lookup'):
                words = subject_words(path, event.text)
                if words:
                    found = design_lookup.report(kit.path('memory'), words,
                                                 [kit.resolve(p) for p in kit.cfg.get('lookup_also') or []],
                                                 int(kit.cfg.get('lookup_max_files', 8)))
                    if found:
                        return kit.context('Design lookup for this brief (quote the governing lines in its Design section):\n' + found)
            if report_rx.fullmatch(path) and event.tool == 'write' and event.tool_name != 'apply_patch' and kit.on('handback'):
                final = (kit.cfg.get('handback') or {}).get('final_status', r'^STATUS: (review|blocked|done)')
                if re.search(final, event.text.lstrip().split('\n', 1)[0]):
                    return handback_answer(event.text, kit, f'writing {path}')
        return None

    if event.tool == 'handback' and kit.on('handback'):
        return handback_answer(event.text, kit, 'handing back')
    return None


def handback_answer(text, kit, where):
    problems = handback_problems(text, kit)
    if not problems:
        return None
    limit = int((kit.cfg.get('handback') or {}).get('max_refusals', 2))
    refused = kit.state.get('handback_refusals', 0)
    if refused >= limit:
        kit.log('passed.log', f'{where} | let through after {refused} refusals, still missing: ' + '; '.join(problems))
        return {'notice': f'Hook brief-and-handback: a hand-back went through after {refused} refusals, still missing: ' + '; '.join(problems)}
    kit.state['handback_refusals'] = refused + 1
    kit.log('refused.log', f'{where} | ' + '; '.join(problems))
    return kit.deny(f'Hand-back not ready ({where}): ' + '; '.join(problems) + '. Add what is missing and send it again. '
                    f'This is refusal {refused + 1} of {limit}; after that the hand-back goes through and the gap is logged.')


if __name__ == '__main__':
    sys.exit(hookkit.main('brief-and-handback', handle))
