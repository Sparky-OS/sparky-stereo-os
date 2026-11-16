#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""queue-keeper: one state file for the work queue, and a gate in front of every lane.

The queue's state is one tab-separated file, one row per item and one status per item. The journal (what happened,
when) is a different file and never says what is open. This hook shows the state at every session start and prompt,
refuses to start a lane the gate does not allow, marks a started lane in flight, and holds an acceptance open until
the row changed. README.md beside this file has the schema, the gate's rule, the configuration and the reasons.

  session start, prompt     what the requester asked and is still open, oldest first; hand-backs waiting for a review;
                            acceptances not yet written to the state; items in flight whose lane is not running
  before a dispatch         the lane's row passes the gate or the dispatch is refused with the reason
  after a dispatch          the lane's row becomes in flight
  after a journal write     an acceptance the journal names whose row did not change is owed, and says so

The same file is a command line: hook.py [--config FILE] next | show | add | set | ahead | gate | audit | context | init.
"""
import argparse
import datetime
import fcntl
import os
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import hookkit  # noqa: E402

NAME = 'queue-keeper'
COLS = ['id', 'name', 'origin', 'asked', 'tier', 'status', 'ahead', 'evidence', 'updated']
COMMANDS = ('next', 'show', 'add', 'set', 'ahead', 'gate', 'audit', 'context', 'init')
OPEN, FLIGHT, REVIEW = 'open', 'in-flight', 'review'   # the three statuses the machinery itself depends on
ID_NUMBER = re.compile(r'\d+')
DEFAULTS = {
    'owner_origin': 'owner',
    'owner_name': 'the requester',
    'origins': ['owner', 'follow-up', 'finding', 'security', 'breakage', 'round', 'outreach', 'machinery'],
    'jump_origins': ['security', 'breakage', 'round'],
    'tiers': ['foundation', 'upstream', 'own', 'later', '-'],
    'statuses': ['open', 'in-flight', 'review', 'staged', 'published', 'done', 'parked', 'waiting-owner', 'merged',
                 'superseded', 'unknown'],
    'closed_statuses': ['published', 'done', 'merged', 'superseded'],
    'slots': 4,
    'state_file': 'queue:QUEUE.tsv',
    'journal': 'queue:ORDER.md',
    'on_missing_state': 'refuse',
    'owed_acceptance': 'refuse',
    'handbacks_waiting': 'tell',
    'stale_hours': 12,
    'running_marker': '.active',
    'launch_patterns': [],
    'brief_pattern': r'(?:BRIEF[^/\s"\'`]*|AGENTS)\.md',
    'lane_id_pattern': r'-([A-Za-z]?\d+[a-z]*\d*[a-z]*)$',
    'match_lane_by_id': True,
    'lane_rows': {},
    'id_pattern': r'^[A-Za-z]?\d+[a-z]*\d*[a-z]*$',
    'acceptance_patterns': [
        r'(?i)\b(?:ORDER|item)\s+#?(?P<id>[A-Za-z]?\d+[a-z]*\d*)\b[^\n]{0,60}?\b(?:accepted|merged|published|staged|closed)\b',
        r'(?i)(?<![\w:.-])(?P<id>[A-Za-z]?\d+[a-z]*\d*)\s+(?:milestone\s+\w+\s+)?(?:accepted|merged|published|staged|closed)\b',
        r'(?i)\b(?:accepted|merged|published|staged|closed)\s*(?:\([^)]*\))?:?\s*(?:ORDER|item)?\s*#?(?P<id>[A-Za-z]?\d+[a-z]*\d*)\b',
    ],
    'report_handed_back': r'^STATUS: (review|blocked)',
    'report_working': r'^STATUS: working',
    'report_accepted': r'^STATUS: (accepted|done)',
    'journal_scan_chars': 6000,
    'context_open_listed': 8,
    'max_listed': 12,
    'audit_folders': 'briefed',
    'audit_ignore': [],
}


class StateError(Exception):
    """The state file cannot be used, and the message says how to get one."""


def opt(kit, key):
    return kit.cfg.get(key, DEFAULTS[key])


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')


def id_number(ident):
    m = ID_NUMBER.search(ident)
    return int(m.group()) if m else 10 ** 9


def first_line(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.readline().strip()
    except OSError:
        return None


class Queue:
    """The state file, the lane folders beside it and the rules over them, from one hook configuration."""

    def __init__(self, kit):
        self.kit = kit
        self.file = kit.resolve(opt(kit, 'state_file'))
        self.journal = kit.resolve(opt(kit, 'journal'))
        self.lanes = kit.path('queue')
        self.owner = opt(kit, 'owner_name')
        self.owner_origin = opt(kit, 'owner_origin')
        self.tiers = list(opt(kit, 'tiers'))
        self.statuses = list(opt(kit, 'statuses'))
        self.origins = list(opt(kit, 'origins'))
        self.closed = set(opt(kit, 'closed_statuses'))

    # ---------------------------------------------------------------- the file
    def how_to_start(self):
        return (f'Rebuild it: {self.file} is one header line and one row per item. '
                f'`python3 {os.path.abspath(__file__)} --config {self.kit.config_path} init` writes the header; '
                f'`... add ID NAME ORIGIN ASKED TIER` adds a row; the lane folders and the journal say what the rows were.')

    def load(self):
        """(rows, problems). Raises StateError when the file is missing, unreadable or has another header."""
        try:
            with open(self.file, encoding='utf-8') as f:
                lines = f.read().splitlines()
        except OSError as e:
            raise StateError(f'the queue state file {self.file} cannot be read ({e.strerror}). {self.how_to_start()}') from e
        if not lines or lines[0].split('\t') != COLS:
            raise StateError(f'the queue state file {self.file} does not start with the header {"<TAB>".join(COLS)}. {self.how_to_start()}')
        rows, problems = [], []
        for n, line in enumerate(lines[1:], 2):
            if not line.strip() or line.startswith('#'):
                continue
            cells = line.split('\t')
            if len(cells) != len(COLS):
                problems.append(f'line {n}: {len(cells)} fields, not {len(COLS)}')
            cells = (cells + [''] * len(COLS))[:len(COLS)]
            rows.append(dict(zip(COLS, cells)))
        return rows, problems

    def save(self, rows):
        rows.sort(key=lambda r: (id_number(r['id']), r['id']))
        text = '\t'.join(COLS) + '\n' + ''.join(
            '\t'.join(r[c].replace('\t', ' ').replace('\n', ' ') for c in COLS) + '\n' for r in rows)
        tmp = f'{self.file}.{os.getpid()}.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(tmp, self.file)

    def mutate(self, change):
        """Read the rows again behind a lock, let `change(rows)` alter them, write them back; returns its result."""
        os.makedirs(self.kit.state_dir, exist_ok=True)
        with open(os.path.join(self.kit.state_dir, 'queue.lock'), 'w') as lock:
            for _ in range(50):
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise StateError('the queue state is being written by another run and the lock stayed busy for 5 s: run it again')
            rows, _ = self.load()
            result = change(rows)
            self.save(rows)
            return result

    @staticmethod
    def find(rows, ident):
        return next((r for r in rows if r['id'] == ident), None)

    def order_key(self, r):
        tier = self.tiers.index(r['tier']) if r['tier'] in self.tiers else len(self.tiers)
        return (r['asked'] or '9999', tier, id_number(r['id']), r['id'])

    def owner_open(self, rows):
        return sorted((r for r in rows if r['origin'] == self.owner_origin and r['status'] == OPEN), key=self.order_key)

    # ---------------------------------------------------------------- lanes
    def row_of_lane(self, rows, lane):
        """The row a lane folder belongs to: the folder is the row's name, or NAME-ID; else, when allowed, the id the
        folder name ends in. The name comes first, so a lane called kernel-build-17 is not item 17."""
        lane = lane.rstrip('/').split('/')[-1]
        mapped = (opt(self.kit, 'lane_rows') or {}).get(lane)
        if mapped:
            return self.find(rows, str(mapped))
        for r in rows:
            if r['name'] and lane in (r['name'], f"{r['name']}-{r['id']}"):
                return r
        if opt(self.kit, 'match_lane_by_id'):
            m = re.search(opt(self.kit, 'lane_id_pattern'), lane)
            if m:
                return self.find(rows, m.group(1))
        return None

    def lane_dir(self, r):
        for folder in (f"{r['name']}-{r['id']}", r['name']):
            path = os.path.join(self.lanes, folder)
            if r['name'] and os.path.isdir(path):
                return path
        return None

    def report_line(self, r):
        folder = self.lane_dir(r)
        return None if folder is None else first_line(os.path.join(folder, 'REPORT.md'))

    def running(self, r):
        """A lane runs when its folder has the marker, or something in it changed within `stale_hours`."""
        folder = self.lane_dir(r)
        if folder is None:
            return False
        if os.path.exists(os.path.join(folder, opt(self.kit, 'running_marker'))):
            return True
        newest = 0.0
        try:
            for entry in list(os.scandir(folder))[:500]:
                newest = max(newest, entry.stat().st_mtime)
            newest = max(newest, os.path.getmtime(folder))
        except OSError:
            return False
        return time.time() - newest < float(opt(self.kit, 'stale_hours')) * 3600

    def updated_ago_hours(self, r):
        try:
            when = datetime.datetime.strptime(r['updated'], '%Y-%m-%dT%H:%MZ').replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            return None
        return (time.time() - when.timestamp()) / 3600

    def stale(self, rows):
        """Items in flight whose lane is not running and whose row has not changed for `stale_hours`."""
        limit = float(opt(self.kit, 'stale_hours'))
        out = []
        for r in rows:
            if r['status'] != FLIGHT or self.running(r):
                continue
            age = self.updated_ago_hours(r)
            if age is None or age >= limit:
                out.append(r)
        return out

    def handed_back(self, rows):
        """(row, REPORT first line) for each item whose lane handed back and whose review has not been recorded."""
        rx = re.compile(opt(self.kit, 'report_handed_back'))
        out = []
        for r in rows:
            if r['status'] in (FLIGHT, REVIEW):
                line = self.report_line(r)
                if line is not None and rx.search(line):
                    out.append((r, line))
                elif r['status'] == REVIEW:
                    out.append((r, line or 'no REPORT.md'))
        return out

    # ---------------------------------------------------------------- the gate
    def gate(self, rows, lane):
        """(allowed, why). The rule is in README.md; each branch below is one line of it."""
        r = self.row_of_lane(rows, lane)
        o = self.owner
        if r is None:
            return False, (f'{lane}: no row in {self.file}. Nothing runs outside the queue: add the row first '
                           f'(hook.py add ID NAME ORIGIN ASKED TIER), with its true origin.')
        if r['origin'] not in self.origins:
            return False, f"{r['id']} {r['name']}: origin '{r['origin']}' is not one of {self.origins}; correct the row."
        if r['status'] in self.closed:
            return False, f"{r['id']} {r['name']} is {r['status']} in the queue ({r['evidence'][:80]}): a new piece of work gets its own row."
        if r['origin'] in opt(self.kit, 'jump_origins'):
            return True, f"{r['id']} {r['name']} goes ahead as {r['origin']}: say so to {o} when you report it."
        waiting = self.owner_open(rows)
        slots = int(opt(self.kit, 'slots'))
        older = '; '.join(f"{w['id']} {w['name']} ({w['asked']})" for w in waiting[:slots])
        if r['origin'] == self.owner_origin:
            if r['status'] != OPEN or r['id'] in [w['id'] for w in waiting[:slots]]:
                return True, f"{r['id']} {r['name']}: {o}'s request of {r['asked']}, in its turn."
            if r['ahead']:
                return True, f"{r['id']} {r['name']} goes ahead of older requests by a recorded reason: {r['ahead']}"
            return False, (f"{r['id']} {r['name']} is {o}'s request of {r['asked']}, but older requests of {o} are open and not in "
                           f"flight: {older}. Start those first, or record {o}'s word with hook.py ahead {r['id']} \"...\".")
        if r['ahead']:
            return True, f"{r['id']} {r['name']} ({r['origin']}) goes ahead by a recorded reason: {r['ahead']}"
        if waiting:
            return False, (f"{r['id']} {r['name']} is a {r['origin']}, and {len(waiting)} of {o}'s own requests are open and not in "
                           f"flight, oldest: {older}. A queue serves who came first. Start one of those; or, if this is "
                           f"{'/'.join(opt(self.kit, 'jump_origins'))}, set its origin truthfully; or, if {o} said it goes first, "
                           f"record the words with hook.py ahead {r['id']} \"...\".")
        return True, f"{r['id']} {r['name']} ({r['origin']}): none of {o}'s own requests is waiting for a lane."

    # ---------------------------------------------------------------- what a person is shown
    def context(self, rows, owed=(), n=None):
        o = self.owner
        n = int(opt(self.kit, 'context_open_listed')) if n is None else n
        cap = int(opt(self.kit, 'max_listed'))
        out = []
        for ident, text in owed:
            out.append(f'ACCEPTANCE NOT COMPLETE: {text}')
        handed = self.handed_back(rows)
        if handed:
            out.append(f'HAND-BACKS WAITING FOR A REVIEW ({len(handed)}); a review comes before a new lane and costs none:')
            for r, line in handed[:cap]:
                out.append(f"  {r['id']} {r['name']} ({r['origin']}, row {r['status']}): {line[:60]}")
            if len(handed) > cap:
                out.append(f'  ... and {len(handed) - cap} more')
        stale = self.stale(rows)
        if stale:
            hours = opt(self.kit, 'stale_hours')
            out.append(f'STALE, in flight and nothing running (no {opt(self.kit, "running_marker")} marker, nothing changed in the lane folder for {hours} h): '
                       + '; '.join(f"{r['id']} {r['name']}" for r in stale[:cap])
                       + ('' if len(stale) <= cap else f' ... and {len(stale) - cap} more')
                       + '. Hand it back, relaunch it or set its status.')
        waiting = self.owner_open(rows)
        out.append(f"QUEUE ({self.file}): {len(waiting)} of {o}'s own requests are open and not in flight. A free lane goes to the oldest "
                   f"of these before anything newer; only {', '.join(opt(self.kit, 'jump_origins'))} go ahead, and are named to {o}:")
        for w in waiting[:n]:
            out.append(f"  {w['id']} {w['name']}, asked {w['asked']}: {w['evidence'][:110]}")
        if len(waiting) > n:
            out.append(f'  ... and {len(waiting) - n} more (hook.py next {len(waiting)})')
        flying = [r for r in rows if r['status'] in (FLIGHT, REVIEW)]
        if flying:
            out.append('In flight: ' + '; '.join(f"{r['id']} {r['name']} ({r['origin']}, {r['status']})" for r in flying[:cap]))
        try:
            age = (time.time() - os.path.getmtime(self.file)) / 3600
            if age > 24:
                out.append(f'The state file was last written {age:.0f} h ago: every launch, hand-back and acceptance changes its row (hook.py set).')
        except OSError:
            pass
        out.append(f"In every status report to {o}: the oldest open requests, and what took each free lane.")
        return out

    # ---------------------------------------------------------------- the audit
    def audit(self, rows, problems):
        out = list(problems)
        seen = set()
        id_rx = re.compile(opt(self.kit, 'id_pattern'))
        working = re.compile(opt(self.kit, 'report_working'))
        accepted = re.compile(opt(self.kit, 'report_accepted'))
        handed = re.compile(opt(self.kit, 'report_handed_back'))
        marker = opt(self.kit, 'running_marker')
        for r in rows:
            label = f"{r['id']} {r['name']}"
            if r['id'] in seen:
                out.append(f'{label}: the id has more than one row')
            seen.add(r['id'])
            if not id_rx.match(r['id']):
                out.append(f"{label}: the id does not match {opt(self.kit, 'id_pattern')}")
            if r['origin'] not in self.origins:
                out.append(f"{label}: origin '{r['origin']}' is not one of {self.origins}")
            if r['status'] not in self.statuses:
                out.append(f"{label}: status '{r['status']}' is not one of {self.statuses}")
            if not re.fullmatch(r'\d{4}-\d\d-\d\d', r['asked']) and (r['asked'] or r['origin'] == self.owner_origin):
                out.append(f"{label}: asked '{r['asked']}' is not a date, YYYY-MM-DD"
                           + (f" (an item's order is the date of {self.owner}'s words)" if r['origin'] == self.owner_origin else ''))
            if r['tier'] not in self.tiers:
                out.append(f"{label}: tier '{r['tier']}' is not one of {self.tiers}")
            line = self.report_line(r) or ''
            folder = self.lane_dir(r)
            if r['status'] in (OPEN, 'parked', 'unknown') and working.search(line):
                out.append(f"{label}: {r['status']} in the queue, but {os.path.basename(folder)}/REPORT.md says {line[:40]}")
            if r['status'] == FLIGHT and accepted.search(line):
                out.append(f"{label}: in flight in the queue, but {os.path.basename(folder)}/REPORT.md says {line[:40]}")
            if r['status'] == FLIGHT and handed.search(line):
                out.append(f"{label}: handed back ({line[:40]}) and not reviewed")
            if r['status'] in self.closed and folder and os.path.exists(os.path.join(folder, marker)):
                out.append(f"{label}: {r['status']} in the queue, but its lane folder still has the {marker} marker")
        for r in self.stale(rows):
            out.append(f"{r['id']} {r['name']}: in flight, and its lane is not running (updated {r['updated']})")
        known = {r['name'] for r in rows if r['name']} | {f"{r['name']}-{r['id']}" for r in rows}
        mode = opt(self.kit, 'audit_folders')
        ignore = set(opt(self.kit, 'audit_ignore'))
        marker_name = opt(self.kit, 'running_marker')
        try:
            for entry in sorted(os.scandir(self.lanes), key=lambda e: e.name):
                if not entry.is_dir() or entry.name.startswith('.') or entry.name in ignore:
                    continue
                briefed = any(os.path.exists(os.path.join(entry.path, f)) for f in ('BRIEF.md', 'AGENTS.md', 'REPORT.md'))
                marked = os.path.exists(os.path.join(entry.path, marker_name))
                if mode == 'all' or (mode == 'active' and marked) or (mode == 'briefed' and (briefed or marked)):
                    if entry.name not in known and self.row_of_lane(rows, entry.name) is None:
                        out.append(f'{entry.name}: a lane folder with no row in the queue')
        except OSError as e:
            out.append(f'the lanes folder {self.lanes} cannot be read ({e.strerror})')
        return out


# -------------------------------------------------------------------- the hook

LANE_SHAPE = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*')


def dispatch_lanes(event, q):
    """(the lane folders a dispatch names or a launch command line starts, the lane names it cannot read). A brief
    path under the lanes folder names a lane; a launch pattern's group is the folder, and a group that is not a
    plain folder name (a shell variable, a substitution) cannot be judged."""
    kit = q.kit
    found, unreadable = [], []
    if event.tool == 'dispatch':
        base = re.escape(q.lanes)
        rel = r'(?<![\w/.-])' + re.escape(os.path.basename(q.lanes))
        rx = re.compile(r'(?:' + base + '|' + rel + r')/([A-Za-z0-9._-]+)/' + opt(kit, 'brief_pattern'))
        found = rx.findall(event.text)
    elif event.tool == 'shell' and opt(kit, 'launch_patterns'):
        commands = event.commands()
        if commands is None:   # a line that cannot be read as shell is searched as text: better a gate too many than one missed
            candidates = [event.acting_command()]
        else:                  # each command's own words up to the first quoted text: an echo of a launch line is no launch
            candidates = []
            for words in commands:
                head = []
                for word in words:
                    if re.search(r'\s', word):
                        break
                    head.append(word)
                candidates.append(' '.join(head))
        for pattern in opt(kit, 'launch_patterns'):
            for candidate in candidates:
                for m in re.findall(pattern, candidate):
                    lane = (m if isinstance(m, str) else m[0]).rstrip(';&|)"\'`')
                    (found if LANE_SHAPE.fullmatch(lane) else unreadable).append(lane)
    return sorted(set(found)), sorted(set(unreadable))


def journal_text(event, q):
    """The text a tool call adds to the journal, or None when the call does not write it."""
    base = re.escape(os.path.basename(q.journal))
    if event.tool in ('write', 'edit'):
        if os.path.normpath(q.journal) in [os.path.normpath(p) for p in event.paths]:
            limit = int(opt(q.kit, 'journal_scan_chars'))
            return event.text[-limit:] if event.tool_name == 'Write' else event.text
        return None
    if event.tool == 'shell' and re.search(r'(?:>>?|\btee\b(?:\s+-a)?)\s*["\']?\S*' + base, event.command):
        return event.command
    return None


def accepted_ids(text, q, rows):
    """Ids the text calls accepted whose row still says open, in flight or in review."""
    found = []
    for pattern in opt(q.kit, 'acceptance_patterns'):
        for m in re.finditer(pattern, text):
            r = q.find(rows, m.group('id'))
            if r and r['status'] in (OPEN, FLIGHT, REVIEW) and r['id'] not in found:
                found.append(r['id'])
    return found


def owed_now(q, rows, kit):
    """The acceptances this session wrote to the journal whose rows have not changed since; changed ones are dropped."""
    owed = kit.state.get('owed') or {}
    live = []
    for ident, then in list(owed.items()):
        r = q.find(rows, ident)
        if r is None or (r['status'], r['updated'], r['evidence']) != (then['status'], then['updated'], then['evidence']):
            del owed[ident]
            continue
        live.append((ident, f"the journal calls {ident} {r['name']} accepted, and its row still says {r['status']} "
                            f"(since {r['updated']}). Change the row in the same step: hook.py set {ident} STATUS \"evidence\" "
                            f"(the same status again with the reason in the evidence, if the journal line was not an acceptance)."))
    kit.state['owed'] = owed
    return live


def handle(event, kit):
    if event.agent and kit.cfg.get('lanes_exempt', True):
        return None   # a lane never dispatches and never writes the queue: its own calls are not the gate's business
    q = Queue(kit)
    if event.kind in ('session-start', 'prompt'):
        if not kit.on('session_start' if event.kind == 'session-start' else 'prompt'):
            return None
        try:
            rows, _ = q.load()
        except StateError as e:
            return kit.context(f'QUEUE: {e}')
        return kit.context('\n'.join(q.context(rows, owed_now(q, rows, kit))))

    if event.kind == 'before-tool':
        if not kit.on('gate'):
            return None
        lanes, unreadable = dispatch_lanes(event, q)
        if unreadable:
            kit.log('refused.log', f'launch names its lane through {unreadable}')
            return kit.deny('QUEUE GATE. This launch names its lane through a shell variable or a substitution '
                            f'({", ".join(unreadable)}), which the gate cannot read, so it cannot be checked against the queue. '
                            'Name the lane in the command itself, one launch per line, and send it again.')
        return gate_answer(event, q, kit, lanes) if lanes else None

    if event.kind == 'after-tool':
        lanes = dispatch_lanes(event, q)[0] if kit.on('mark_in_flight') else []
        text = journal_text(event, q) if kit.on('journal') else None
        if not lanes and text is None:
            return None
        try:
            rows, _ = q.load()
        except StateError as e:
            return kit.context(f'QUEUE: {e}')
        notes = []
        if lanes:
            notes += mark_in_flight(q, lanes, kit)
        if text is not None:
            ids = accepted_ids(text, q, rows)
            owed = kit.state.setdefault('owed', {})
            for ident in ids:
                r = q.find(rows, ident)
                owed[ident] = {'status': r['status'], 'updated': r['updated'], 'evidence': r['evidence']}
            if ids:
                kit.log('owed.log', 'journal names ' + ', '.join(ids) + ' accepted; rows unchanged')
                notes += [f'ACCEPTANCE NOT COMPLETE: the journal calls {i} accepted and its row still says '
                          f"{q.find(rows, i)['status']}. The acceptance is not done until the row changed: "
                          f'hook.py set {i} staged|published|done "evidence", and add a row for every follow-up it queued, '
                          f'with its true origin.' for i in ids]
        return kit.context('\n'.join(notes)) if notes else None
    return None


def gate_answer(event, q, kit, lanes):
    try:
        rows, _ = q.load()
    except StateError as e:
        kit.log('refused.log', f'{lanes}: state unusable: {e}')
        if opt(kit, 'on_missing_state') == 'tell':
            return kit.context(f'QUEUE GATE could not check {", ".join(lanes)}: {e} The dispatch goes ahead because the '
                               f'configuration says on_missing_state: tell.')
        return kit.deny(f'QUEUE GATE: {e}')
    refused, said = [], []
    mode = opt(kit, 'owed_acceptance')
    owed = owed_now(q, rows, kit) if mode != 'off' else []
    if owed:
        text = ' '.join(t for _, t in owed)
        (refused if mode == 'refuse' else said).append(f'ACCEPTANCE NOT COMPLETE: {text}')
    for lane in lanes:
        ok, why = q.gate(rows, lane)
        (said if ok else refused).append(why)
    mode = opt(kit, 'handbacks_waiting')
    if mode != 'off':
        starting = {q.row_of_lane(rows, lane)['id'] for lane in lanes if q.row_of_lane(rows, lane)}
        waiting = [(r, line) for r, line in q.handed_back(rows) if r['id'] not in starting]
        if waiting:
            text = (f'{len(waiting)} hand-back(s) wait for a review, which costs no lane: '
                    + '; '.join(f"{r['id']} {r['name']}" for r, _ in waiting[:int(opt(kit, 'max_listed'))]) + '.')
            (refused if mode == 'refuse' else said).append(text)
    if refused:
        kit.log('refused.log', f'{lanes}: ' + ' | '.join(refused))
        return kit.deny('QUEUE GATE. ' + ' '.join(refused))
    kit.log('passed.log', f'{lanes}: ' + ' | '.join(said))
    return kit.context('QUEUE GATE passed. ' + ' '.join(said) + ' Its row becomes in flight when the dispatch succeeds; '
                       'set it again at the hand-back and at the acceptance.')


def mark_in_flight(q, lanes, kit):
    def change(rows):
        marked = []
        for lane in lanes:
            r = q.row_of_lane(rows, lane)
            if r and r['status'] in (OPEN, 'unknown', 'parked', REVIEW):
                r['status'], r['updated'] = FLIGHT, stamp()
                marked.append(f"{r['id']} {r['name']}")
        return marked
    try:
        marked = q.mutate(change)
    except (StateError, OSError) as e:
        kit.log('errors.log', f'could not mark {lanes} in flight: {e}')
        return [f'QUEUE: the dispatch ran, but its row could not be marked in flight ({e}). Run hook.py set ID in-flight.']
    return [f'QUEUE: now in flight: {", ".join(marked)}.'] if marked else []


# -------------------------------------------------------------------- the command line

def cli_command(argv):
    skip = False
    for word in argv:
        if skip:
            skip = False
        elif word in ('--config', '--dialect'):
            skip = True
        elif not word.startswith('-'):
            return word if word in COMMANDS else None
    return None


def cli(argv):
    ap = argparse.ArgumentParser(prog='hook.py', description='The queue keeper\'s command line. Exit status: 0 done or allowed, '
                                 '1 refused or findings, 2 the state or the configuration cannot be used.')
    ap.add_argument('--config', help='the configuration file (default: SPARKY_HOOKS_CONFIG_DIR or SPARKY_WORKSPACE, as the hook)')
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('next', help='the requester\'s open requests oldest first, then what is in flight')
    p.add_argument('count', nargs='?', type=int)
    sub.add_parser('context', help='the lines a session start shows')
    p = sub.add_parser('show', help='one row')
    p.add_argument('id')
    p = sub.add_parser('add', help='a new row, status open')
    p.add_argument('id')
    p.add_argument('name')
    p.add_argument('origin')
    p.add_argument('asked', help='the date of the requester\'s words for an owner request, the filing date otherwise (YYYY-MM-DD)')
    p.add_argument('tier')
    p.add_argument('evidence', nargs='?', default='')
    p = sub.add_parser('set', help='a launch, a hand-back, an acceptance, a parking: change a row\'s status')
    p.add_argument('id')
    p.add_argument('status')
    p.add_argument('evidence', nargs='?')
    p = sub.add_parser('ahead', help='record why an item goes ahead of the queue (the words quoted); no reason removes it')
    p.add_argument('id')
    p.add_argument('reason', nargs='?', default='')
    p = sub.add_parser('gate', help='allow or refuse a lane folder, with the reason')
    p.add_argument('lane')
    sub.add_parser('audit', help='rows and lane folders that disagree, items never updated, folders with no row')
    sub.add_parser('init', help='write the header of a new state file')
    argv, config = list(argv), None
    if '--config' in argv and argv.index('--config') + 1 < len(argv):   # the option may stand anywhere, as the command does
        at = argv.index('--config')
        config = argv[at + 1]
        del argv[at:at + 2]
    a = ap.parse_args(argv)
    a.config = a.config or config
    try:
        config_path = a.config or hookkit.find_config(NAME, [])
        cfg = hookkit.load_config(config_path)
        kit = hookkit.Kit(NAME, cfg, config_path)
        q = Queue(kit)
        return run_command(a, q)
    except (hookkit.HookError, StateError) as e:
        print(f'queue-keeper: {e}', file=sys.stderr)
        return 2


def run_command(a, q):
    owner = q.owner
    if a.command == 'init':
        if os.path.exists(q.file):
            print(f'queue-keeper: {q.file} exists; nothing written', file=sys.stderr)
            return 1
        os.makedirs(os.path.dirname(q.file), exist_ok=True)
        with open(q.file, 'w', encoding='utf-8') as f:
            f.write('\t'.join(COLS) + '\n')
        print(f'wrote {q.file}')
        return 0
    rows, problems = q.load()
    if a.command in ('next', 'context'):
        print('\n'.join(q.context(rows, n=a.count if a.command == 'next' else None)))
        return 0
    if a.command == 'show':
        r = q.find(rows, a.id)
        print('\n'.join(f'{c}: {r[c]}' for c in COLS) if r else f'{a.id}: no row')
        return 0 if r else 1
    if a.command == 'add':
        if not re.match(opt(q.kit, 'id_pattern'), a.id):
            raise StateError(f"the id must match {opt(q.kit, 'id_pattern')}")
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', a.name):
            raise StateError('the name is letters, digits, dot, dash and underscore (it is also the lane folder\'s name)')
        if a.origin not in q.origins:
            raise StateError(f'origin must be one of {q.origins}; an item {owner} did not ask for is never origin {q.owner_origin}')
        if a.tier not in q.tiers:
            raise StateError(f'tier must be one of {q.tiers}')
        if not re.fullmatch(r'\d{4}-\d\d-\d\d', a.asked):
            raise StateError('asked is a date, YYYY-MM-DD')

        def add(rows):
            if q.find(rows, a.id):
                raise StateError(f'{a.id} already has a row')
            rows.append(dict(id=a.id, name=a.name, origin=a.origin, asked=a.asked, tier=a.tier, status=OPEN, ahead='',
                             evidence=a.evidence, updated=stamp()))
        q.mutate(add)
        return 0
    if a.command in ('set', 'ahead'):
        if a.command == 'set' and a.status not in q.statuses:
            raise StateError(f'status must be one of {q.statuses}')

        def change(rows):
            r = q.find(rows, a.id)
            if r is None:
                raise StateError(f'{a.id}: no row')
            if a.command == 'set':
                r['status'] = a.status
                if a.evidence is not None:
                    r['evidence'] = a.evidence
            else:
                r['ahead'] = a.reason
            r['updated'] = stamp()
        q.mutate(change)
        return 0
    if a.command == 'gate':
        ok, why = q.gate(rows, a.lane)
        print(('ALLOW: ' if ok else 'REFUSE: ') + why)
        return 0 if ok else 1
    if a.command == 'audit':
        found = q.audit(rows, problems)
        print('\n'.join(found) if found else 'queue audit: nothing found')
        return 1 if found else 0
    return 2


if __name__ == '__main__':
    if cli_command(sys.argv[1:]):   # a command anywhere in the arguments: it must not wait for an event on stdin
        sys.exit(cli(sys.argv[1:]))
    sys.exit(hookkit.main(NAME, handle))
