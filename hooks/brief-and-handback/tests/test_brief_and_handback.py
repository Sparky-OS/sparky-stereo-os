#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the brief-and-handback hook. Run: python3 hooks/tests/run.py brief-and-handback"""
import os
import sys
import time
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

GOOD_REPORT = 'STATUS: review\n\n## Design check\nRead: ...\n\n## Corpus consulted\n...\n\n## Skill changes\n...\n'


class Dispatch(testkit.HookCase):
    hook = 'brief-and-handback'

    def lane(self, name, text=None):
        return testkit.write(os.path.join(self.ws, 'partners', 'queue', name, 'BRIEF.md'), text if text is not None else testkit.GOOD_BRIEF)

    def dispatch(self, prompt, tool='Agent', **kw):
        return self.event('PreToolUse', tool, {'description': 'a lane', 'prompt': prompt}, **kw)

    def test_a_complete_brief_is_dispatched_with_the_reminder(self):
        out = self.run_hook(self.dispatch(f'Your brief is {self.lane("good-lane")}: read it in full first.'))
        self.assertIsNone(self.decision(out))
        self.assertIn('its hand-back carries a Design check', self.added_context(out))

    def test_each_missing_part_of_a_brief_is_named(self):
        cases = {
            'no "## Design" section': testkit.GOOD_BRIEF.replace('## Design\n', '## Notes\n'),
            'no "## The skill to leave behind" section': testkit.GOOD_BRIEF.replace('## The skill to leave behind\n', '## Later\n'),
            'its Design section names no memory file': testkit.GOOD_BRIEF.replace('one-format-inside.md', 'the contract'),
            'its Design section quotes nothing': testkit.GOOD_BRIEF.replace('"One format inside, output only full side by side"', 'one format inside'),
            'it does not ask for "Design check" in the hand-back': testkit.GOOD_BRIEF.replace('Design check, ', ''),
            'it does not ask for "Skill changes" in the hand-back': testkit.GOOD_BRIEF.replace(', Skill changes', ''),
        }
        for n, (problem, text) in enumerate(cases.items()):
            with self.subTest(problem):
                path = self.lane(f'lane-{n}', text)
                out = self.run_hook(self.dispatch(f'Brief: {path}'))
                self.assertEqual(self.decision(out), 'deny')
                self.assertIn(f'{path}: {problem}', self.reason(out))
                self.assertIn('then dispatch again', self.reason(out))
        self.assertIn('dispatch | ', self.log('refused.log'))

    def test_headings_are_found_in_their_usual_spellings(self):
        for n, heading in enumerate(('## Skill to leave behind', '### The skills to leave behind', '## the skill to leave behind (public)')):
            with self.subTest(heading):
                path = self.lane(f'spelling-{n}', testkit.GOOD_BRIEF.replace('## The skill to leave behind', heading))
                self.assertIsNone(self.decision(self.run_hook(self.dispatch(f'Brief: {path}'))))

    def test_a_brief_that_cannot_be_read_stops_the_dispatch(self):
        missing = os.path.join(self.ws, 'partners', 'queue', 'ghost-lane', 'BRIEF.md')
        out = self.run_hook(self.dispatch(f'Brief: {missing}'))
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn('it cannot be read', self.reason(out))

    def test_a_dispatch_that_names_no_brief_passes(self):
        out = self.run_hook(self.dispatch('Find where the menu is drawn and report the file.'))
        self.assertIsNone(self.decision(out))

    def test_a_brief_outside_the_queue_is_not_this_hook_s_business(self):
        other = testkit.write(os.path.join(self.ws, 'private', 'drafts', 'x', 'BRIEF.md'), '# nothing\n')
        self.assertIsNone(self.decision(self.run_hook(self.dispatch(f'Brief: {other}'))))

    def test_agents_md_counts_as_a_brief_and_task_as_a_dispatch(self):
        path = testkit.write(os.path.join(self.ws, 'partners', 'queue', 'codex-lane', 'AGENTS.md'), '# bare\n')
        self.assertEqual(self.decision(self.run_hook(self.dispatch(f'Brief: {path}', tool='Task'))), 'deny')

    def test_switches(self):
        path = self.lane('bad-lane', '# bare\n')
        self.configure(on={'dispatch': False})
        self.assertIsNone(self.run_hook(self.dispatch(f'Brief: {path}')))
        self.configure(on={'dispatch': True, 'dispatch_reminder': False})
        self.assertIsNone(self.run_hook(self.dispatch(f'Brief: {self.lane("fine-lane")}')))
        self.configure(brief={'design_names_a_memory': False, 'design_quotes': False, 'headings': ['Design'], 'must_say': []})
        self.assertIsNone(self.run_hook(self.dispatch(f'Brief: {self.lane("short-lane", "# t\n\n## Design\nplain\n")}')))


class BriefWrite(testkit.HookCase):
    hook = 'brief-and-handback'

    def test_writing_a_brief_shows_the_memory_files_that_hold_its_subject(self):
        path = os.path.join(self.ws, 'partners', 'queue', 'languages-menu', 'BRIEF.md')
        out = self.run_hook(self.event('PreToolUse', 'Write', {'file_path': path, 'content': '# Languages of the display menu\n'}))
        text = self.added_context(out)
        self.assertIn('Design lookup for this brief', text)
        self.assertIn(self.memory('required-languages.md'), text)
        self.assertIn(self.memory('display-design.md'), text)
        self.assertIsNone(self.decision(out))

    def test_found_by_content_not_by_file_name(self):
        path = os.path.join(self.ws, 'partners', 'queue', 'fallback-audit', 'BRIEF.md')
        out = self.run_hook(self.event('PreToolUse', 'Write', {'file_path': path, 'content': '# Audit\n'}))
        self.assertIn(self.memory('check-every-default.md'), self.added_context(out))  # "fallback" is only in its text

    def test_nothing_found_says_nothing_and_other_files_are_left_alone(self):
        path = os.path.join(self.ws, 'partners', 'queue', 'zzz-qqq', 'BRIEF.md')
        self.assertIsNone(self.run_hook(self.event('PreToolUse', 'Write', {'file_path': path, 'content': '# Xyzzy\n'})))
        notes = os.path.join(self.ws, 'partners', 'queue', 'languages-menu', 'NOTES.md')
        self.assertIsNone(self.run_hook(self.event('PreToolUse', 'Write', {'file_path': notes, 'content': '# Languages\n'})))


class Handback(testkit.HookCase):
    hook = 'brief-and-handback'

    def handback(self, message, **kw):
        return self.event('PreToolUse', 'SubagentHandback', {'message': message}, agent='agent-3', **kw)

    def test_a_complete_report_is_delivered(self):
        self.assertIsNone(self.run_hook(self.handback(GOOD_REPORT)))

    def test_a_report_without_its_sections_is_refused_with_what_is_missing(self):
        out = self.run_hook(self.handback('All done, everything works.'))
        self.assertEqual(self.decision(out), 'deny')
        for part in ('its first line is not a status line', 'no "Design check" section', 'no "Corpus consulted" section',
                     'no "Skill changes" section', 'refusal 1 of 2'):
            self.assertIn(part, self.reason(out))

    def test_after_the_limit_the_report_goes_through_and_the_gap_is_logged(self):
        bad = 'STATUS: review\n\n## Design check\n...\n'
        self.assertEqual(self.decision(self.run_hook(self.handback(bad))), 'deny')
        self.assertEqual(self.decision(self.run_hook(self.handback(bad))), 'deny')
        out = self.run_hook(self.handback(bad))
        self.assertIsNone(self.decision(out))
        self.assertIn('went through after 2 refusals', out['systemMessage'])
        self.assertIn('let through after 2 refusals, still missing: no "Corpus consulted" section', self.log('passed.log'))

    def test_a_final_report_written_to_the_lane_folder_is_checked_and_a_working_one_is_not(self):
        path = os.path.join(self.ws, 'partners', 'queue', 'demo-lane', 'REPORT.md')
        write = lambda text: self.event('PreToolUse', 'Write', {'file_path': path, 'content': text})
        self.assertEqual(self.decision(self.run_hook(write('STATUS: review\n\nDone.\n'))), 'deny')
        self.assertIsNone(self.run_hook(write('STATUS: working\n\nSo far.\n')))
        self.assertIsNone(self.run_hook(write(GOOD_REPORT)))
        elsewhere = os.path.join(self.ws, 'private', 'drafts', 'REPORT.md')
        self.assertIsNone(self.run_hook(self.event('PreToolUse', 'Write', {'file_path': elsewhere, 'content': 'STATUS: review\n'})))

    def test_the_switch_turns_it_off(self):
        self.configure(on={'handback': False})
        self.assertIsNone(self.run_hook(self.handback('nothing')))


class WaitingLanes(testkit.HookCase):
    hook = 'brief-and-handback'

    def report(self, lane, first_line, age_days=0):
        path = testkit.write(os.path.join(self.ws, 'partners', 'queue', lane, 'REPORT.md'), first_line + '\n\nText.\n')
        if age_days:
            old = time.time() - age_days * 86400
            os.utime(path, (old, old))

    def test_the_coordinator_is_told_which_lanes_wait(self):
        self.report('alpha', 'STATUS: review (milestone 2)')
        self.report('beta', 'STATUS: working')
        self.report('gamma', 'STATUS: blocked: no disk')
        self.report('old', 'STATUS: review', age_days=5)
        text = self.added_context(self.run_hook(self.event('SessionStart', source='compact')))
        self.assertEqual(text, 'Lanes waiting for a review now: alpha (STATUS: review (milestone 2)); gamma (STATUS: blocked: no disk).')

    def test_a_lane_is_not_told_and_nothing_waiting_says_nothing(self):
        self.report('alpha', 'STATUS: review')
        self.assertIsNone(self.run_hook(self.event('SessionStart', source='startup', agent='agent-1')))
        self.configure(on={'waiting_lanes': False})
        self.assertIsNone(self.run_hook(self.event('SessionStart', source='startup')))


if __name__ == '__main__':
    unittest.main()
