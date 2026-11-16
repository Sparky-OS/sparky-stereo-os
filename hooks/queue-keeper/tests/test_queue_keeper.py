#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the queue-keeper hook. Run: python3 hooks/tests/run.py queue-keeper

Every queue here is made in the test's temporary workspace: a state file, lane folders and a journal. Each rule of
the gate is run red and green; the missing state, a lane's own call, the journal and the audit have their own tests,
and the dialect of Codex is run on the same cases as Claude Code's.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hook.py')
COLS = ['id', 'name', 'origin', 'asked', 'tier', 'status', 'ahead', 'evidence', 'updated']
LONG_AGO = '2026-01-01T00:00Z'


def row(ident, name, origin='owner', asked='2026-10-01', tier='own', status='open', ahead='', evidence='', updated=None):
    updated = updated or time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime())
    return [ident, name, origin, asked, tier, status, ahead, evidence, updated]


class QueueCase(testkit.HookCase):
    hook = 'queue-keeper'

    def setUp(self):
        super().setUp()
        self.queue = os.path.join(self.ws, 'partners', 'queue')
        self.state = os.path.join(self.queue, 'QUEUE.tsv')
        self.journal = os.path.join(self.queue, 'ORDER.md')
        shutil.rmtree(os.path.join(self.queue, 'demo-lane'))
        self.configure(launch_patterns=[r'launch-lane\.sh\s+(?:queue/)?(\S+)'])

    # making the queue
    def put(self, *rows):
        os.makedirs(self.queue, exist_ok=True)
        with open(self.state, 'w', encoding='utf-8') as f:
            f.write('\t'.join(COLS) + '\n' + ''.join('\t'.join(r) + '\n' for r in rows))

    def table(self):
        with open(self.state, encoding='utf-8') as f:
            lines = f.read().splitlines()
        return {c[0]: dict(zip(COLS, c)) for c in (line.split('\t') for line in lines[1:])}

    def lane(self, name, report=None, active=False, age_hours=0.0):
        folder = os.path.join(self.queue, name)
        os.makedirs(folder, exist_ok=True)
        testkit.write(os.path.join(folder, 'BRIEF.md'), testkit.GOOD_BRIEF)
        if report is not None:
            testkit.write(os.path.join(folder, 'REPORT.md'), report + '\n\nthe rest\n')
        if active:
            open(os.path.join(folder, '.active'), 'w').close()
        if age_hours:
            old = time.time() - age_hours * 3600
            for entry in os.listdir(folder):
                os.utime(os.path.join(folder, entry), (old, old))
            os.utime(folder, (old, old))
        return folder

    # events
    def brief_of(self, lane):
        return os.path.join(self.queue, lane, 'BRIEF.md')

    def dispatch(self, lane, phase='PreToolUse', tool='Agent', **kw):
        return self.event(phase, tool, {'description': 'a lane', 'prompt': f'Your brief is {self.brief_of(lane)}: read it first.'}, **kw)

    def launch(self, lane, phase='PreToolUse', **kw):
        return self.bash(f'sh partners/launch-lane.sh queue/{lane}', phase=phase, **kw)

    def prompt(self, **kw):
        return self.event('UserPromptSubmit', prompt='go on', **kw)

    def journal_edit(self, text, **kw):
        return self.event('PostToolUse', 'Edit', {'file_path': self.journal, 'old_string': 'x', 'new_string': text}, **kw)

    def cli(self, *args, expect=0):
        r = subprocess.run([sys.executable, '-B', HOOK, '--config', self.config, *args], capture_output=True, text=True, timeout=60,
                           env={k: v for k, v in os.environ.items() if not k.startswith('SPARKY_')})
        self.assertEqual(r.returncode, expect, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def refused(self, out, *words):
        self.assertEqual(self.decision(out), 'deny', out)
        for w in words:
            self.assertIn(w, self.reason(out))
        return self.reason(out)

    def passed(self, out):
        self.assertIsNone(self.decision(out), out)
        return self.added_context(out)


class Gate(QueueCase):
    """Each line of the gate's rule, refused and allowed."""

    def setUp(self):
        super().setUp()
        for lane in ('old-one-1', 'old-two-2', 'old-three-3', 'old-four-4', 'old-five-5', 'new-owner-6', 'fix-it-7', 'sec-8',
                     'follow-9', 'nothing-here-99'):
            self.lane(lane)
        self.put(row('1', 'old-one', asked='2026-09-01'), row('2', 'old-two', asked='2026-09-02'),
                 row('3', 'old-three', asked='2026-09-03'), row('4', 'old-four', asked='2026-09-04'),
                 row('5', 'old-five', asked='2026-09-05'), row('6', 'new-owner', asked='2026-11-01'),
                 row('7', 'fix-it', origin='breakage', asked='2026-11-10'), row('8', 'sec', origin='security', asked='2026-11-11'),
                 row('9', 'follow', origin='follow-up', asked='2026-11-12'),
                 row('10', 'finished', origin='finding', status='done', evidence='abc123'))

    def test_a_lane_with_no_row_is_refused_and_told_how_to_add_it(self):
        out = self.run_hook(self.dispatch('nothing-here-99'))
        self.refused(out, 'no row in', 'Nothing runs outside the queue', 'hook.py add ID NAME ORIGIN ASKED TIER')

    def test_a_finished_item_is_refused_so_new_work_gets_its_own_row(self):
        self.lane('finished-10')
        self.refused(self.run_hook(self.dispatch('finished-10')), 'is done in the queue', 'its own row')

    def test_breakage_and_security_go_ahead_and_are_said(self):
        for lane, origin in (('fix-it-7', 'breakage'), ('sec-8', 'security')):
            with self.subTest(origin):
                text = self.passed(self.run_hook(self.dispatch(lane)))
                self.assertIn(f'goes ahead as {origin}', text)
                self.assertIn('say so to the requester', text)

    def test_the_round_origin_goes_ahead_too(self):
        self.lane('blocker-11')
        self.put(row('1', 'old-one'), row('11', 'blocker', origin='round'))
        self.assertIn('goes ahead as round', self.passed(self.run_hook(self.dispatch('blocker-11'))))

    def test_the_four_oldest_requests_of_the_owner_start_in_their_turn(self):
        for lane in ('old-one-1', 'old-four-4'):
            with self.subTest(lane):
                self.assertIn("in its turn", self.passed(self.run_hook(self.dispatch(lane))))

    def test_the_fifth_request_waits_for_the_four_older_ones(self):
        reason = self.refused(self.run_hook(self.dispatch('old-five-5')), "older requests of the requester are open and not in flight",
                              '1 old-one (2026-09-01)', '4 old-four (2026-09-04)', 'hook.py ahead 5')
        self.assertNotIn('5 old-five (', reason)

    def test_the_number_of_slots_is_the_owner_s_to_set(self):
        self.configure(slots=1)
        self.refused(self.run_hook(self.dispatch('old-two-2')), '1 old-one')
        self.passed(self.run_hook(self.dispatch('old-one-1')))
        self.configure(slots=6)
        self.passed(self.run_hook(self.dispatch('new-owner-6')))

    def test_a_younger_request_goes_ahead_only_by_a_recorded_reason(self):
        self.refused(self.run_hook(self.dispatch('new-owner-6')), 'older requests of the requester')
        self.put(*[row(r['id'], r['name'], r['origin'], r['asked'], r['tier'], r['status'],
                       ahead='the requester: do this one first' if r['id'] == '6' else '') for r in self.table().values()])
        self.assertIn('by a recorded reason: the requester: do this one first', self.passed(self.run_hook(self.dispatch('new-owner-6'))))

    def test_a_request_already_started_is_resumed_in_its_turn(self):
        self.put(row('1', 'old-one'), row('2', 'old-two'), row('3', 'old-three'), row('4', 'old-four'), row('5', 'old-five'),
                 row('6', 'new-owner', status='parked', asked='2026-11-01'))
        self.passed(self.run_hook(self.dispatch('new-owner-6')))

    def test_a_follow_up_waits_while_a_request_of_the_owner_waits(self):
        self.refused(self.run_hook(self.dispatch('follow-9')), 'is a follow-up', '6 of the requester', 'oldest: 1 old-one',
                     'A queue serves who came first', 'security/breakage/round')

    def test_a_follow_up_goes_with_a_recorded_reason_and_when_nothing_waits(self):
        self.put(row('9', 'follow', origin='follow-up', ahead='the requester said so'))
        self.assertIn('recorded reason: the requester said so', self.passed(self.run_hook(self.dispatch('follow-9'))))
        self.put(row('9', 'follow', origin='follow-up'), row('1', 'old-one', status='in-flight'))
        self.assertIn('none of the requester\'s own requests is waiting', self.passed(self.run_hook(self.dispatch('follow-9'))))

    def test_an_origin_the_schema_does_not_know_is_refused(self):
        self.put(row('9', 'follow', origin='whim'))
        self.refused(self.run_hook(self.dispatch('follow-9')), "origin 'whim' is not one of")

    def test_the_owner_s_origin_name_is_configurable(self):
        self.configure(owner_origin='asker', owner_name='Alex', origins=['asker', 'follow-up', 'security', 'breakage', 'round'])
        self.put(*[row(r['id'], r['name'], 'asker' if r['origin'] == 'owner' else r['origin'], r['asked'], r['tier'], r['status'])
                   for r in self.table().values()])
        reason = self.refused(self.run_hook(self.dispatch('follow-9')), "6 of Alex's own requests")
        self.assertNotIn('the requester', reason)

    def test_a_lane_folder_finds_its_row_by_name_first(self):
        self.lane('kernel-build-17')
        self.put(row('17', 'old-seventeen', asked='2026-09-01'), row('627', 'kernel-build-17', origin='security', asked='2026-11-16'))
        self.assertIn('627 kernel-build-17 goes ahead as security', self.passed(self.run_hook(self.dispatch('kernel-build-17'))))

    def test_a_lane_folder_finds_its_row_by_the_id_it_ends_in(self):
        self.lane('whatever-name-12b')
        self.put(row('12b', 'the-real-name', origin='security'))
        self.assertIn('12b the-real-name', self.passed(self.run_hook(self.dispatch('whatever-name-12b'))))
        self.configure(match_lane_by_id=False)
        self.refused(self.run_hook(self.dispatch('whatever-name-12b')), 'no row in')

    def test_a_lane_folder_the_naming_cannot_find_is_mapped_by_the_configuration(self):
        self.lane('oldest-name-for-it')
        self.refused(self.run_hook(self.dispatch('oldest-name-for-it')), 'no row in')
        self.configure(lane_rows={'oldest-name-for-it': '7'})
        self.assertIn('7 fix-it goes ahead as breakage', self.passed(self.run_hook(self.dispatch('oldest-name-for-it'))))
        self.assertNotIn('oldest-name-for-it: a lane folder with no row', self.cli('audit', expect=1))

    def test_a_dispatch_that_names_no_lane_passes(self):
        out = self.run_hook(self.event('PreToolUse', 'Agent', {'prompt': 'Find where the menu is drawn.'}))
        self.assertIsNone(out)

    def test_a_relative_brief_path_counts(self):
        out = self.run_hook(self.event('PreToolUse', 'Agent', {'prompt': 'Read queue/nothing-here-99/BRIEF.md first.'}))
        self.refused(out, 'no row in')

    def test_every_lane_a_dispatch_names_is_judged(self):
        prompt = f'Briefs: {self.brief_of("old-one-1")} and {self.brief_of("nothing-here-99")}'
        out = self.run_hook(self.event('PreToolUse', 'Agent', {'prompt': prompt}))
        self.refused(out, 'nothing-here-99: no row')
        self.assertIn('refused.log', os.listdir(os.path.join(self.ws, 'state', 'hooks', 'queue-keeper')))

    def test_a_launch_command_passes_the_same_gate(self):
        self.refused(self.run_hook(self.launch('nothing-here-99')), 'no row in')
        self.passed(self.run_hook(self.launch('old-one-1')))

    def test_a_launch_that_names_its_lane_through_a_variable_is_refused_as_unreadable(self):
        lines = ['sh partners/launch-lane.sh queue/$LANE',
                 'LANE=old-one-1; sh partners/launch-lane.sh queue/"$LANE"',
                 'sh partners/launch-lane.sh "queue/$(cat next-lane.txt)"',
                 'for l in old-one-1 old-two-2; do sh partners/launch-lane.sh queue/${l}; done',
                 'sh partners/launch-lane.sh queue/`pick`',
                 'echo "unbalanced; sh partners/launch-lane.sh queue/$LANE']          # cannot be read as shell: searched as text
        for line in lines:
            with self.subTest(line):
                self.refused(self.run_hook(self.bash(line)), 'names its lane through a shell variable or a substitution',
                             'Name the lane in the command itself, one launch per line')
        self.assertIn('launch names its lane through', self.log('refused.log'))

    def test_a_literal_lane_in_quotes_or_after_other_words_is_judged_not_refused_as_unreadable(self):
        for line in ('sh partners/launch-lane.sh "queue/old-one-1"', "sh partners/launch-lane.sh 'queue/old-one-1' ; echo $HOME",
                     'cd partners && sh launch-lane.sh queue/old-one-1 && echo started', 'sh partners/launch-lane.sh old-one-1',
                     'timeout 5 sh partners/launch-lane.sh queue/old-one-1 >/dev/null 2>&1'):
            with self.subTest(line):
                self.assertIn('old-one', self.passed(self.run_hook(self.bash(line))))

    def test_a_post_event_of_an_unreadable_launch_marks_nothing(self):
        self.assertIsNone(self.run_hook(self.bash('sh partners/launch-lane.sh queue/$LANE', phase='PostToolUse')))

    def test_a_command_that_only_mentions_a_launch_is_not_a_launch(self):
        self.assertIsNone(self.run_hook(self.bash('echo "run launch-lane.sh queue/nothing-here-99 later"  # launch-lane.sh queue/x')))

    def test_a_lane_s_own_call_is_not_the_gate_s_business(self):
        self.assertIsNone(self.run_hook(self.dispatch('nothing-here-99', agent='lane-7')))
        self.assertIsNone(self.run_hook(self.prompt(agent='lane-7')))
        self.configure(lanes_exempt=False)
        self.refused(self.run_hook(self.dispatch('nothing-here-99', agent='lane-7')), 'no row in')

    def test_the_gate_can_be_switched_off(self):
        self.configure(on={'gate': False})
        self.assertIsNone(self.run_hook(self.dispatch('nothing-here-99')))


class MissingState(QueueCase):
    def remove_state(self):
        os.unlink(self.state)

    def test_a_missing_file_refuses_the_dispatch_and_says_how_to_rebuild_it(self):
        self.remove_state()
        self.lane('a-lane-1')
        out = self.run_hook(self.dispatch('a-lane-1'))
        reason = self.refused(out, 'cannot be read', 'Rebuild it', 'init', 'add ID NAME ORIGIN ASKED TIER')
        self.assertIn(self.state, reason)
        self.assertIn('state unusable', self.log('refused.log'))

    def test_the_configuration_may_choose_to_tell_instead_and_it_is_said(self):
        self.remove_state()
        self.lane('a-lane-1')
        self.configure(on_missing_state='tell')
        text = self.passed(self.run_hook(self.dispatch('a-lane-1')))
        self.assertIn('could not check a-lane-1', text)
        self.assertIn('on_missing_state: tell', text)

    def test_the_session_start_says_it_too(self):
        self.remove_state()
        text = self.added_context(self.run_hook(self.event('SessionStart', source='startup')))
        self.assertIn('QUEUE:', text)
        self.assertIn('cannot be read', text)

    def test_another_header_is_not_a_queue(self):
        testkit.write(self.state, 'id\tname\n1\ta\n')
        self.lane('a-lane-1')
        self.refused(self.run_hook(self.dispatch('a-lane-1')), 'does not start with the header')

    def test_a_queue_with_a_header_and_no_rows_is_a_queue_and_refuses_what_has_no_row(self):
        self.cli('init', expect=1)      # install.py init already wrote the header
        self.remove_state()
        self.cli('init', expect=0)
        self.cli('init', expect=1)
        self.lane('a-lane-1')
        self.refused(self.run_hook(self.dispatch('a-lane-1')), 'no row in')
        self.cli('add', '1', 'a-lane', 'owner', '2026-11-01', 'own', 'the first request')
        self.passed(self.run_hook(self.dispatch('a-lane-1')))

    def test_install_init_makes_the_header_so_a_new_queue_starts_empty(self):
        with open(self.state, encoding='utf-8') as f:
            self.assertEqual(f.read().split('\n')[0].split('\t'), COLS)


class Shown(QueueCase):
    """What the session start and every prompt show."""

    def test_the_owner_s_open_requests_come_oldest_first_whatever_their_number(self):
        self.put(row('600', 'newer-number-older-date', asked='2026-10-01', evidence='the early one'),
                 row('20', 'older-number-newer-date', asked='2026-10-15'), row('21', 'follow', origin='follow-up'))
        text = self.added_context(self.run_hook(self.prompt()))
        self.assertLess(text.index('600 newer-number-older-date'), text.index('20 older-number-newer-date'))
        self.assertIn("2 of the requester's own requests are open and not in flight", text)
        self.assertIn('the early one', text)
        self.assertNotIn('21 follow', text.split('In flight')[0])

    def test_the_tier_orders_equal_dates(self):
        self.put(row('1', 'low', tier='own'), row('2', 'high', tier='foundation'))
        text = self.added_context(self.run_hook(self.prompt()))
        self.assertLess(text.index('2 high'), text.index('1 low'))

    def test_session_start_and_prompt_show_the_same_state(self):
        self.put(row('1', 'first'))
        a = self.added_context(self.run_hook(self.event('SessionStart', source='startup')))
        b = self.added_context(self.run_hook(self.prompt()))
        self.assertEqual(a, b)
        self.assertIn('1 first', a)

    def test_what_is_in_flight_is_shown_with_its_origin(self):
        self.put(row('1', 'first', status='in-flight'), row('2', 'second', origin='security', status='in-flight'))
        text = self.added_context(self.run_hook(self.prompt()))
        self.assertIn('In flight: 1 first (owner, in-flight); 2 second (security, in-flight)', text)

    def test_a_long_list_is_cut_and_says_how_to_see_the_rest(self):
        self.put(*[row(str(n), f'item-{n}', asked=f'2026-10-{n:02d}') for n in range(1, 21)])
        text = self.added_context(self.run_hook(self.prompt()))
        self.assertIn('... and 12 more (hook.py next 20)', text)

    def test_a_state_not_written_for_a_day_is_said(self):
        self.put(row('1', 'first'))
        old = time.time() - 30 * 3600
        os.utime(self.state, (old, old))
        self.assertIn('last written 30 h ago', self.added_context(self.run_hook(self.prompt())))

    def test_the_switches_silence_a_part(self):
        self.put(row('1', 'first'))
        self.configure(on={'prompt': False})
        self.assertIsNone(self.run_hook(self.prompt()))
        self.assertIn('1 first', self.added_context(self.run_hook(self.event('SessionStart', source='startup'))))
        self.configure(enabled=False)
        self.assertIsNone(self.run_hook(self.event('SessionStart', source='startup')))


class HandBacks(QueueCase):
    def test_a_hand_back_waiting_is_shown_at_every_prompt_until_the_row_is_set(self):
        self.lane('done-work-5', report='STATUS: review')
        self.put(row('5', 'done-work', status='in-flight'), row('6', 'other', status='in-flight'))
        for _ in range(3):
            text = self.added_context(self.run_hook(self.prompt()))
            self.assertIn('HAND-BACKS WAITING FOR A REVIEW (1)', text)
            self.assertIn('5 done-work (owner, row in-flight): STATUS: review', text)
            self.assertTrue(text.startswith('HAND-BACKS'))     # first, before the requests
        self.cli('set', '5', 'staged', 'reviewed')
        self.assertNotIn('HAND-BACKS', self.added_context(self.run_hook(self.prompt())))

    def test_a_blocked_report_waits_too_and_a_working_one_does_not(self):
        self.lane('a-lane-5', report='STATUS: blocked on the rig')
        self.lane('b-lane-6', report='STATUS: working')
        self.put(row('5', 'a-lane', status='in-flight'), row('6', 'b-lane', status='in-flight'))
        text = self.added_context(self.run_hook(self.prompt()))
        self.assertIn('5 a-lane', text.split('QUEUE')[0])
        self.assertNotIn('6 b-lane', text.split('QUEUE')[0])

    def test_a_row_in_review_is_waiting_even_without_a_report(self):
        self.put(row('5', 'a-lane', status='review'))
        self.assertIn('5 a-lane (owner, row review): no REPORT.md', self.added_context(self.run_hook(self.prompt())))

    def test_a_dispatch_is_told_by_default_and_refused_when_the_configuration_says_so(self):
        self.lane('done-work-5', report='STATUS: review')
        self.lane('next-up-6')
        self.put(row('5', 'done-work', status='in-flight'), row('6', 'next-up', origin='security'))
        self.assertIn('1 hand-back(s) wait for a review, which costs no lane: 5 done-work', self.passed(self.run_hook(self.dispatch('next-up-6'))))
        self.configure(handbacks_waiting='refuse')
        self.refused(self.run_hook(self.dispatch('next-up-6')), 'hand-back(s) wait for a review', '5 done-work')
        self.configure(handbacks_waiting='off')
        self.assertNotIn('wait for a review', self.passed(self.run_hook(self.dispatch('next-up-6'))))

    def test_the_review_itself_may_relaunch_its_lane(self):
        self.lane('done-work-5', report='STATUS: review')
        self.put(row('5', 'done-work', status='review'))
        self.configure(handbacks_waiting='refuse')
        self.passed(self.run_hook(self.dispatch('done-work-5')))


class Stale(QueueCase):
    def put_flight(self, **kw):
        self.put(row('5', 'long-gone', status='in-flight', updated=kw.get('updated', LONG_AGO)))

    def text(self):
        return self.added_context(self.run_hook(self.prompt()))

    def test_in_flight_with_no_marker_and_a_silent_folder_is_stale(self):
        self.lane('long-gone-5', report='STATUS: working', age_hours=30)
        self.put_flight()
        text = self.text()
        self.assertIn('STALE, in flight and nothing running', text)
        self.assertIn('5 long-gone', text)
        self.assertIn('Hand it back, relaunch it or set its status', text)

    def test_a_marker_or_recent_work_or_a_recent_row_keeps_it_running(self):
        self.lane('long-gone-5', active=True, age_hours=30)
        self.put_flight()
        self.assertNotIn('STALE', self.text())
        os.unlink(os.path.join(self.queue, 'long-gone-5', '.active'))
        old = time.time() - 30 * 3600
        os.utime(os.path.join(self.queue, 'long-gone-5'), (old, old))     # removing the marker touched the folder
        self.assertIn('STALE', self.text())
        testkit.write(os.path.join(self.queue, 'long-gone-5', 'evidence', 'a.log'), 'fresh\n')
        os.utime(os.path.join(self.queue, 'long-gone-5', 'evidence', 'a.log'))
        os.utime(os.path.join(self.queue, 'long-gone-5'))
        self.assertNotIn('STALE', self.text())

    def test_a_row_just_set_in_flight_is_not_stale_before_its_lane_writes(self):
        self.lane('long-gone-5', age_hours=30)
        self.put_flight(updated=time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime()))
        self.assertNotIn('STALE', self.text())

    def test_an_item_in_flight_with_no_lane_folder_at_all_is_stale_once_its_row_is_old(self):
        self.put_flight()
        self.assertIn('STALE', self.text())

    def test_the_marker_and_the_hours_are_configurable(self):
        self.lane('long-gone-5', age_hours=30)
        open(os.path.join(self.queue, 'long-gone-5', '.running'), 'w').close()
        old = time.time() - 30 * 3600
        os.utime(os.path.join(self.queue, 'long-gone-5', '.running'), (old, old))
        os.utime(os.path.join(self.queue, 'long-gone-5'), (old, old))
        self.put_flight()
        self.configure(running_marker='.running')
        self.assertNotIn('STALE', self.text())
        self.configure(running_marker='.other', stale_hours=48)
        self.assertNotIn('STALE', self.text())


class MarkInFlight(QueueCase):
    def setUp(self):
        super().setUp()
        for lane in ('one-1', 'two-2', 'done-3'):
            self.lane(lane)
        self.put(row('1', 'one'), row('2', 'two', origin='breakage', status='parked'), row('3', 'done', origin='finding', status='done'))

    def test_a_dispatch_that_succeeded_marks_the_row_in_flight(self):
        self.run_hook(self.dispatch('one-1', phase='PostToolUse'))
        row_one = self.table()['1']
        self.assertEqual(row_one['status'], 'in-flight')
        self.assertRegex(row_one['updated'], r'^\d{4}-\d\d-\d\dT\d\d:\d\dZ$')

    def test_the_post_event_says_what_it_marked(self):
        text = self.added_context(self.run_hook(self.dispatch('two-2', phase='PostToolUse')))
        self.assertIn('now in flight: 2 two', text)
        self.assertEqual(self.table()['2']['status'], 'in-flight')

    def test_a_refused_dispatch_changes_nothing(self):
        self.refused(self.run_hook(self.dispatch('done-3')), 'is done')
        self.assertEqual(self.table()['3']['status'], 'done')
        self.assertEqual(self.table()['1']['status'], 'open')    # the gate itself writes nothing

    def test_a_finished_row_is_not_reopened_by_a_post_event(self):
        self.run_hook(self.dispatch('done-3', phase='PostToolUse'))
        self.assertEqual(self.table()['3']['status'], 'done')

    def test_a_launch_command_marks_its_row_too(self):
        self.run_hook(self.launch('one-1', phase='PostToolUse'))
        self.assertEqual(self.table()['1']['status'], 'in-flight')

    def test_other_rows_and_fields_are_kept_byte_for_byte(self):
        before = self.table()
        self.run_hook(self.dispatch('one-1', phase='PostToolUse'))
        after = self.table()
        self.assertEqual({k: v for k, v in after.items() if k != '1'}, {k: v for k, v in before.items() if k != '1'})
        self.assertEqual({k: v for k, v in after['1'].items() if k not in ('status', 'updated')},
                         {k: v for k, v in before['1'].items() if k not in ('status', 'updated')})

    def test_it_can_be_switched_off(self):
        self.configure(on={'mark_in_flight': False})
        self.run_hook(self.dispatch('one-1', phase='PostToolUse'))
        self.assertEqual(self.table()['1']['status'], 'open')

    def test_an_unwritable_state_is_said_and_not_hidden(self):
        os.chmod(self.queue, 0o555)
        self.addCleanup(os.chmod, self.queue, 0o755)
        if os.access(self.queue, os.W_OK):
            self.skipTest('the folder is writable for this user (root)')
        out = self.run_hook(self.dispatch('one-1', phase='PostToolUse'))
        self.assertIn('could not be marked in flight', self.added_context(out))
        self.assertIn('could not mark', self.log('errors.log'))


class Owed(QueueCase):
    """An acceptance is not complete until the row changed."""

    def setUp(self):
        super().setUp()
        self.lane('next-up-9')
        self.put(row('5', 'the-work', status='review', evidence='handed back'), row('6', 'other', status='in-flight'),
                 row('9', 'next-up', origin='security'), row('7', 'closed-one', status='staged'))
        testkit.write(self.journal, '# journal\n')

    def owed(self):
        return self.added_context(self.run_hook(self.prompt()))

    def test_a_journal_line_that_calls_an_item_accepted_leaves_it_owed(self):
        text = self.added_context(self.run_hook(self.journal_edit('- 2026-11-16 18:24 UTC: 5 ACCEPTED (lane): all checks green.')))
        self.assertIn('ACCEPTANCE NOT COMPLETE', text)
        self.assertIn('5', text)
        self.assertIn('hook.py set 5 staged|published|done', text)
        self.assertIn('a row for every follow-up', text)
        self.assertIn('5 the-work', self.owed())
        self.assertTrue(self.owed().startswith('ACCEPTANCE NOT COMPLETE'))

    def test_the_dispatch_is_refused_until_the_row_changed(self):
        self.run_hook(self.journal_edit('ORDER 5 accepted, merged.'))
        self.refused(self.run_hook(self.dispatch('next-up-9')), 'ACCEPTANCE NOT COMPLETE', 'the journal calls 5 the-work accepted',
                     'hook.py set 5 STATUS')
        self.cli('set', '5', 'staged', 'stage with sums')
        self.assertNotIn('ACCEPTANCE', self.owed())
        self.passed(self.run_hook(self.dispatch('next-up-9')))

    def test_a_row_set_in_the_same_step_before_the_journal_is_not_owed(self):
        self.cli('set', '5', 'staged', 'sums')
        self.assertIsNone(self.run_hook(self.journal_edit('ORDER 5 accepted.')))
        self.assertNotIn('ACCEPTANCE', self.owed())

    def test_the_same_status_again_with_a_reason_settles_a_journal_line_that_was_not_an_acceptance(self):
        self.run_hook(self.journal_edit('6 closed the loop on the old question.'))
        self.assertIn('6 other', self.owed())
        self.cli('set', '6', 'in-flight', 'not an acceptance: the journal word was closed')
        self.assertNotIn('ACCEPTANCE', self.owed())

    def test_a_shell_append_to_the_journal_counts_even_through_a_here_document(self):
        command = f"cat >> {self.journal} <<'EOF'\n- 2026-11-16 18:24 UTC: 6 accepted.\nEOF"
        text = self.added_context(self.run_hook(self.bash(command, phase='PostToolUse')))
        self.assertIn('ACCEPTANCE NOT COMPLETE', text)
        self.assertIn('hook.py set 6', text)

    def test_tee_and_a_redirect_to_the_journal_count_a_read_does_not(self):
        for command in (f'echo "ORDER 5 accepted" | tee -a {self.journal}', 'echo "ORDER 5 accepted" >> partners/queue/ORDER.md'):
            with self.subTest(command):
                self.assertIn('ACCEPTANCE NOT COMPLETE', self.added_context(self.run_hook(self.bash(command, phase='PostToolUse'))))
        self.assertIsNone(self.run_hook(self.bash(f'grep -n "ORDER 5 accepted" {self.journal}', phase='PostToolUse')))
        self.assertIsNone(self.run_hook(self.bash('echo "ORDER 5 accepted" > /tmp/other.md', phase='PostToolUse')))

    def test_a_write_of_the_whole_journal_is_read_by_its_tail_only(self):
        old = '- ORDER 5 accepted (long ago).\n' + 'filler line of the journal\n' * 600
        out = self.run_hook(self.event('PostToolUse', 'Write', {'file_path': self.journal, 'content': old + '- 6 accepted.\n'}))
        text = self.added_context(out)
        self.assertIn('hook.py set 6', text)
        self.assertNotIn('hook.py set 5', text)

    def test_dates_and_numbers_in_a_line_are_not_items(self):
        self.put(row('18', 'eighteen', status='in-flight'), row('24', 'twentyfour', status='in-flight'), row('2026', 'year', status='in-flight'))
        self.assertIsNone(self.run_hook(self.journal_edit('- 2026-11-16 18:24 UTC: the lane was launched and merged nothing yet.')))

    def test_only_an_item_that_can_still_be_accepted_is_owed(self):
        self.assertIsNone(self.run_hook(self.journal_edit('ORDER 7 accepted again.')))     # already staged
        self.assertIsNone(self.run_hook(self.journal_edit('ORDER 404 accepted.')))         # no such row

    def test_the_other_writes_are_not_the_journal(self):
        other = os.path.join(self.queue, 'NOTES.md')
        self.assertIsNone(self.run_hook(self.event('PostToolUse', 'Edit', {'file_path': other, 'old_string': 'x', 'new_string': 'ORDER 5 accepted'})))

    def test_the_configuration_may_tell_instead_of_refusing_or_look_away(self):
        self.run_hook(self.journal_edit('ORDER 5 accepted.'))
        self.configure(owed_acceptance='tell')
        text = self.passed(self.run_hook(self.dispatch('next-up-9')))
        self.assertIn('ACCEPTANCE NOT COMPLETE', text)
        self.configure(owed_acceptance='off')
        self.assertNotIn('ACCEPTANCE', self.passed(self.run_hook(self.dispatch('next-up-9'))))

    def test_it_is_owed_per_session(self):
        self.run_hook(self.journal_edit('ORDER 5 accepted.'))
        self.assertNotIn('ACCEPTANCE', self.added_context(self.run_hook(self.prompt(session='another-session'))))

    def test_the_acceptance_words_are_the_owner_s_to_set(self):
        self.configure(acceptance_patterns=[r'(?i)\bshipped\s+(?P<id>\d+)\b'])
        self.assertIsNone(self.run_hook(self.journal_edit('ORDER 5 accepted.')))
        self.assertIn('hook.py set 5', self.added_context(self.run_hook(self.journal_edit('shipped 5'))))

    def test_the_journal_part_can_be_switched_off(self):
        self.configure(on={'journal': False})
        self.assertIsNone(self.run_hook(self.journal_edit('ORDER 5 accepted.')))


class Dialects(QueueCase):
    """Codex says the same things in its own words for its events and tools."""
    dialect = 'codex'

    def setUp(self):
        super().setUp()
        self.lane('old-one-1')
        self.lane('follow-9')
        self.put(row('1', 'old-one'), row('9', 'follow', origin='follow-up'), row('5', 'the-work', status='in-flight'))

    def test_a_spawned_agent_is_gated_and_the_refusal_is_codex_s_deny(self):
        out = self.run_hook(self.event('PreToolUse', 'spawn_agent', {'prompt': f'Read {self.brief_of("follow-9")}'}))
        self.refused(out, 'is a follow-up')
        self.assertEqual(out['hookSpecificOutput']['hookEventName'], 'PreToolUse')
        self.passed(self.run_hook(self.event('PreToolUse', 'spawn_agent', {'prompt': f'Read {self.brief_of("old-one-1")}'})))

    def test_the_state_is_shown_at_the_session_start_and_every_prompt(self):
        for event in (self.event('SessionStart', source='startup'), self.prompt()):
            self.assertIn('1 old-one', self.added_context(self.run_hook(event)))

    def test_a_patch_to_the_journal_leaves_an_acceptance_owed(self):
        patch = f'*** Begin Patch\n*** Update File: {self.journal}\n@@\n+- ORDER 5 accepted.\n*** End Patch'
        text = self.added_context(self.run_hook(self.event('PostToolUse', 'apply_patch', {'command': patch})))
        self.assertIn('ACCEPTANCE NOT COMPLETE', text)
        self.refused(self.run_hook(self.dispatch('old-one-1', tool='spawn_agent')), 'the journal calls 5 the-work accepted')

    def test_a_launch_by_shell_is_gated(self):
        self.refused(self.run_hook(self.launch('follow-9')), 'is a follow-up')

    def test_the_same_dispatch_gets_the_same_answer_in_both_dialects(self):
        claude = self.run_hook(self.dispatch('follow-9', tool='Agent'), dialect='claude')
        codex = self.run_hook(self.dispatch('follow-9', tool='Agent'), dialect='codex')
        self.assertEqual(claude, codex)


class Audit(QueueCase):
    def setUp(self):
        super().setUp()
        self.base = row('1', 'a-fine-one', status='in-flight')
        self.put(self.base)
        self.lane('a-fine-one-1', report='STATUS: working')

    def audit(self, expect):
        return self.cli('audit', expect=expect)

    def test_a_queue_that_agrees_with_its_folders_finds_nothing(self):
        self.assertEqual(self.audit(0).strip(), 'queue audit: nothing found')

    def test_each_disagreement_is_named_with_both_sides(self):
        cases = [
            (row('2', 'asleep', status='open'), 'asleep-2', 'STATUS: working', "2 asleep: open in the queue, but asleep-2/REPORT.md says STATUS: working"),
            (row('3', 'finished', status='in-flight'), 'finished-3', 'STATUS: accepted', "3 finished: in flight in the queue, but finished-3/REPORT.md says STATUS: accepted"),
            (row('4', 'returned', status='in-flight'), 'returned-4', 'STATUS: review', "4 returned: handed back (STATUS: review) and not reviewed"),
        ]
        for r, folder, report, wanted in cases:
            with self.subTest(wanted):
                self.put(self.base, r)
                self.lane(folder, report=report)
                self.assertIn(wanted, self.audit(1))

    def test_a_finished_row_whose_lane_still_carries_the_marker_is_named(self):
        self.put(self.base, row('2', 'finished', status='done'))
        self.lane('finished-2', active=True)
        self.assertIn("2 finished: done in the queue, but its lane folder still has the .active marker", self.audit(1))

    def test_an_old_review_label_on_a_finished_row_is_not_a_disagreement(self):
        self.put(self.base, row('2', 'finished', status='staged'))
        self.lane('finished-2', report='STATUS: review')
        self.assertEqual(self.audit(0).strip(), 'queue audit: nothing found')

    def test_a_lane_folder_with_no_row_is_named(self):
        self.lane('orphan-77', report='STATUS: working')
        self.assertIn('orphan-77: a lane folder with no row in the queue', self.audit(1))

    def test_which_folders_count_is_the_configuration_s_choice(self):
        os.makedirs(os.path.join(self.queue, 'empty-folder'))
        self.lane('briefed-only-80')
        self.lane('marked-81', active=True)
        out = self.audit(1)
        self.assertIn('briefed-only-80', out)
        self.assertIn('marked-81', out)
        self.assertNotIn('empty-folder', out)
        self.configure(audit_folders='active')
        out = self.audit(1)
        self.assertNotIn('briefed-only-80', out)
        self.assertIn('marked-81', out)
        self.configure(audit_folders='all')
        self.assertIn('empty-folder', self.audit(1))
        self.configure(audit_folders='all', audit_ignore=['empty-folder', 'briefed-only-80', 'marked-81'])
        self.assertEqual(self.audit(0).strip(), 'queue audit: nothing found')

    def test_a_folder_found_by_its_row_s_name_or_trailing_id_is_not_an_orphan(self):
        self.lane('renamed-by-id-1')
        self.assertEqual(self.audit(0).strip(), 'queue audit: nothing found')

    def test_the_state_file_s_own_faults_are_named(self):
        testkit.write(self.state, '\t'.join(COLS) + '\n' + '\t'.join(row('1', 'a-fine-one')) + '\n'
                      + '\t'.join(row('1', 'twice')) + '\n'
                      + '\t'.join(row('x y', 'bad id', origin='whim', asked='yesterday', tier='middle', status='mystery')) + '\n'
                      + 'only\ttwo\n')
        out = self.audit(1)
        for wanted in ('1 twice: the id has more than one row', "origin 'whim' is not one of", "status 'mystery' is not one of",
                       "asked 'yesterday' is not a date", "tier 'middle' is not one of", 'the id does not match', 'line 5: 2 fields, not 9'):
            self.assertIn(wanted, out)

    def test_a_date_is_owed_by_the_owner_s_requests_and_older_rows_of_others_may_lack_it(self):
        self.put(self.base, row('2', 'no-date-follow-up', origin='follow-up', asked=''), row('3', 'no-date-request', asked=''))
        out = self.audit(1)
        self.assertNotIn('2 no-date-follow-up', out)
        self.assertIn("3 no-date-request: asked '' is not a date, YYYY-MM-DD (an item's order is the date of the requester's words)", out)

    def test_a_stale_item_in_flight_is_named(self):
        self.put(row('1', 'a-fine-one', status='in-flight', updated=LONG_AGO))
        self.lane('a-fine-one-1', report='STATUS: working', age_hours=40)
        self.assertIn('1 a-fine-one: in flight, and its lane is not running', self.audit(1))

    def test_a_missing_state_is_exit_2_with_the_way_to_rebuild_it(self):
        os.unlink(self.state)
        out = self.cli('audit', expect=2)
        self.assertIn('cannot be read', out)
        self.assertIn('Rebuild it', out)

    def test_the_audit_changes_nothing(self):
        before = open(self.state, 'rb').read()
        self.cli('audit', expect=0)
        self.assertEqual(open(self.state, 'rb').read(), before)


class CommandLine(QueueCase):
    def setUp(self):
        super().setUp()
        self.put(row('1', 'first', asked='2026-09-01'), row('2', 'second', origin='follow-up'))

    def test_add_set_ahead_and_show(self):
        self.cli('add', '3', 'third-item', 'finding', '2026-11-16', 'foundation', 'seen in the lane report')
        self.assertEqual(self.table()['3']['status'], 'open')
        self.assertEqual(self.table()['3']['evidence'], 'seen in the lane report')
        self.cli('set', '3', 'in-flight')
        self.assertEqual(self.table()['3']['status'], 'in-flight')
        self.assertEqual(self.table()['3']['evidence'], 'seen in the lane report')       # no evidence given: kept
        self.cli('set', '3', 'staged', 'the stage, with sums')
        self.assertEqual(self.table()['3']['evidence'], 'the stage, with sums')
        self.cli('ahead', '3', 'the requester said: this first')
        self.assertIn('ahead: the requester said: this first', self.cli('show', '3'))
        self.cli('ahead', '3')
        self.assertEqual(self.table()['3']['ahead'], '')
        self.assertIn('no row', self.cli('show', '404', expect=1))

    def test_the_rows_are_kept_in_order_of_their_numbers(self):
        self.cli('add', '10', 'tenth', 'finding', '2026-11-16', 'own')
        self.cli('add', '1b', 'first-b', 'finding', '2026-11-16', 'own')
        self.assertEqual(list(self.table()), ['1', '1b', '2', '10'])

    def test_what_is_refused_says_what_is_allowed(self):
        cases = [(('add', '1', 'again', 'finding', '2026-11-16', 'own'), 'already has a row'),
                 (('add', '3', 'x', 'whim', '2026-11-16', 'own'), 'origin must be one of'),
                 (('add', '3', 'x', 'finding', '2026-11-16', 'middle'), 'tier must be one of'),
                 (('add', '3', 'x', 'finding', 'today', 'own'), 'asked is a date'),
                 (('add', 'three three', 'x', 'finding', '2026-11-16', 'own'), 'the id must match'),
                 (('add', '3', 'a b', 'finding', '2026-11-16', 'own'), 'the name is letters'),
                 (('set', '1', 'mystery'), 'status must be one of'),
                 (('set', '404', 'done'), 'no row')]
        for args, wanted in cases:
            with self.subTest(args):
                self.assertIn(wanted, self.cli(*args, expect=2))
        self.assertEqual(sorted(self.table()), ['1', '2'])

    def test_a_tab_or_a_newline_in_a_field_cannot_break_the_file(self):
        self.cli('set', '1', 'done', 'two\tcolumns\nand a line')
        self.assertEqual(self.table()['1']['evidence'], 'two columns and a line')
        self.assertEqual(self.cli('audit', expect=0).strip(), 'queue audit: nothing found')

    def test_gate_prints_allow_or_refuse_and_exits_accordingly(self):
        self.lane('second-2')
        self.assertIn('REFUSE: 2 second is a follow-up', self.cli('gate', 'second-2', expect=1))
        self.assertIn("ALLOW: 1 first: the requester's request", self.cli('gate', 'first-1', expect=0))

    def test_next_and_context_print_the_same_picture_as_the_prompt(self):
        self.assertIn('1 first, asked 2026-09-01', self.cli('next'))
        self.assertEqual(self.cli('context').strip(), self.cli('next').strip())

    def test_the_command_is_found_wherever_it_stands_in_the_arguments(self):
        r = subprocess.run([sys.executable, '-B', HOOK, 'next', '--config', self.config], capture_output=True, text=True, timeout=30, input='')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('1 first', r.stdout)

    def test_eight_writers_at_once_lose_no_row(self):
        procs = [subprocess.Popen([sys.executable, '-B', HOOK, '--config', self.config, 'add', str(100 + n), f'racer-{n}', 'finding',
                                   '2026-11-16', 'own'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for n in range(8)]
        for p in procs:
            out, err = p.communicate(timeout=60)
            self.assertEqual((p.returncode, err), (0, ''), out)
        self.assertEqual(len(self.table()), 10)

    def test_a_configuration_that_cannot_be_read_is_exit_2_not_a_traceback(self):
        r = subprocess.run([sys.executable, '-B', HOOK, '--config', os.path.join(self.tmp, 'absent.json'), 'next'], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 2)
        self.assertIn('cannot read the configuration', r.stderr)
        self.assertNotIn('Traceback', r.stderr)


class HookContract(QueueCase):
    def test_a_broken_configuration_lets_the_action_through_and_says_so(self):
        with open(self.config, 'w') as f:
            f.write('{ not json')
        r = self.run_raw(json.dumps(self.dispatch('x-1')), env={'XDG_STATE_HOME': os.path.join(self.tmp, 'xdg')})
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertIn('could not run and let the action through', out['systemMessage'])
        self.assertNotIn('hookSpecificOutput', out)

    def test_an_unreadable_event_is_said_not_raised(self):
        r = self.run_raw('not json at all', env={'XDG_STATE_HOME': os.path.join(self.tmp, 'xdg')})
        self.assertEqual((r.returncode, r.stderr), (0, ''))
        self.assertIn('could not run', json.loads(r.stdout)['systemMessage'])


if __name__ == '__main__':
    unittest.main()
