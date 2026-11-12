#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the design-reading hook: events piped in, answers read. Run: python3 hooks/tests/run.py design-reading"""
import json
import os
import sys
import time
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402


class DesignReading(testkit.HookCase):
    hook = 'design-reading'

    def state_file(self):
        folder = os.path.join(self.ws, 'state', 'hooks', self.hook)
        return [os.path.join(folder, n) for n in os.listdir(folder) if n.endswith('.json')][0]

    def age_last_call(self, seconds):
        path = self.state_file()
        with open(path) as f:
            state = json.load(f)
        state['last_seen'] -= seconds
        with open(path, 'w') as f:
            json.dump(state, f)

    def read_all(self, names=('check-every-default.md', 'one-format-inside.md'), **kw):
        for name in names:
            self.assertIsNone(self.run_hook(self.read(self.memory(name), **kw)))

    def test_session_start_lists_the_core_files(self):
        out = self.run_hook(self.event('SessionStart', source='compact'))
        text = self.added_context(out)
        self.assertIn('Required reading (session compact)', text)
        self.assertIn(self.memory('check-every-default.md'), text)
        self.assertIn(self.memory('one-format-inside.md'), text)
        self.assertIn('display-design.md (any change to a display or an output)', text)

    def test_tools_are_refused_until_every_file_is_read_in_full(self):
        self.run_hook(self.event('SessionStart', source='startup'))
        out = self.run_hook(self.bash('ls'))
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn(self.memory('one-format-inside.md'), self.reason(out))
        self.assertIn('read in full', self.reason(out))
        # one file read: still refused, and only the other one is listed
        self.run_hook(self.read(self.memory('check-every-default.md')))
        out = self.run_hook(self.bash('ls'))
        self.assertEqual(self.decision(out), 'deny')
        self.assertNotIn('check-every-default.md', self.reason(out))
        # the second read lets tools through, and says so in the log
        self.run_hook(self.read(self.memory('one-format-inside.md')))
        self.assertIsNone(self.run_hook(self.bash('ls')))
        self.assertIn('read all (session startup)', self.log('reads.log'))
        self.assertIn('Bash while 2 unread', self.log('refused.log'))

    def test_a_partial_read_does_not_count(self):
        self.run_hook(self.event('SessionStart', source='startup'))
        self.run_hook(self.read(self.memory('check-every-default.md'), tool_input={'limit': 5}))
        self.run_hook(self.read(self.memory('one-format-inside.md'), tool_input={'offset': 3}))
        self.assertEqual(self.decision(self.run_hook(self.bash('ls'))), 'deny')

    def test_a_file_of_the_same_name_elsewhere_does_not_count(self):
        self.run_hook(self.event('SessionStart', source='startup'))
        other = testkit.write(os.path.join(self.ws, 'private', 'drafts', 'one-format-inside.md'), 'a copy\n')
        self.run_hook(self.read(other))
        self.run_hook(self.read(self.memory('check-every-default.md')))
        self.assertEqual(self.decision(self.run_hook(self.bash('ls'))), 'deny')

    def test_reading_tools_and_listed_prefixes_are_never_refused(self):
        self.run_hook(self.event('SessionStart', source='startup'))
        for tool in ('Read', 'Glob', 'Grep', 'mcp__reference__consult_knowledge'):
            with self.subTest(tool):
                self.assertIsNone(self.run_hook(self.event('PreToolUse', tool, {'file_path': self.memory('MEMORY.md')})))
        for tool in ('Bash', 'Write', 'Edit', 'Agent', 'SubagentHandback', 'WebFetch'):
            with self.subTest(tool):
                self.assertEqual(self.decision(self.run_hook(self.event('PreToolUse', tool, {}))), 'deny')

    def test_first_call_in_a_context_starts_the_reading(self):
        out = self.run_hook(self.bash('ls'))
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn('first call in this context', self.reason(out))

    def test_a_long_gap_starts_the_reading_again(self):
        self.run_hook(self.bash('ls'))
        self.read_all()
        self.assertIsNone(self.run_hook(self.bash('ls')))
        self.age_last_call(3299)
        self.assertIsNone(self.run_hook(self.bash('ls')))
        self.age_last_call(3301)
        out = self.run_hook(self.bash('ls'))
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn('55 minutes since the last call: the context is read cold again', self.reason(out))

    def test_a_prompt_shows_the_list_and_is_not_blocked(self):
        out = self.run_hook(self.event('UserPromptSubmit', prompt='go on'))
        self.assertIn('Required reading (first call in this context)', self.added_context(out))
        self.assertNotIn('decision', out)
        self.read_all()
        self.assertIsNone(self.run_hook(self.event('UserPromptSubmit', prompt='go on')))

    def test_each_session_and_each_agent_has_its_own_list(self):
        self.run_hook(self.bash('ls', session='a'))
        self.read_all(session='a')
        self.assertIsNone(self.run_hook(self.bash('ls', session='a')))
        self.assertEqual(self.decision(self.run_hook(self.bash('ls', session='b'))), 'deny')
        self.assertEqual(self.decision(self.run_hook(self.bash('ls', session='a', agent='agent-7'))), 'deny')

    def test_a_lane_reads_what_its_brief_names_and_what_its_subject_calls_for(self):
        brief = testkit.write(os.path.join(self.ws, 'partners', 'queue', 'menus-lane', 'BRIEF.md'),
                              '# Menus\n\n## Design\nMemory display-design.md: "outputs are filters". Translate every string.\n')
        transcript = os.path.join(self.tmp, 'session-1.jsonl')
        testkit.write(os.path.join(self.tmp, 'session-1', 'subagents', 'agent-agent-9.jsonl'),
                      json.dumps({'message': {'content': [{'type': 'text', 'text': f'Your brief is {brief}: read it first.'}]}}) + '\n')
        out = self.run_hook(self.bash('ls', agent='agent-9', transcript_path=transcript))
        reason = self.reason(out)
        for name in ('check-every-default.md', 'one-format-inside.md', 'display-design.md', 'required-languages.md'):
            self.assertIn(self.memory(name), reason)
        self.assertNotIn('MEMORY.md', reason.replace('memory/MEMORY.md', ''))

    def test_switches_turn_each_trigger_off(self):
        self.configure(on={'session_start': False, 'first_call': False})
        self.assertIsNone(self.run_hook(self.event('SessionStart', source='startup')))
        self.assertIsNone(self.run_hook(self.bash('ls')))
        self.configure(enabled=False, on={'session_start': True, 'first_call': True})
        self.assertIsNone(self.run_hook(self.event('SessionStart', source='startup')))
        self.assertIsNone(self.run_hook(self.bash('ls', session='other')))

    def test_core_files_that_do_not_exist_are_not_demanded(self):
        self.configure(core=['absent.md', 'one-format-inside.md'])
        out = self.run_hook(self.bash('ls'))
        self.assertNotIn('absent.md', self.reason(out))
        self.run_hook(self.read(self.memory('one-format-inside.md')))
        self.assertIsNone(self.run_hook(self.bash('ls')))

    def test_parallel_reads_all_count(self):
        """A tool runs several reads at once, and the hook runs once for each: no read may be lost."""
        import subprocess
        names = [f'fact-{n}.md' for n in range(12)]
        for name in names:
            testkit.write(self.memory(name), 'A fact.\n')
        self.configure(core=names)
        self.run_hook(self.event('SessionStart', source='startup'))
        command = [sys.executable, '-B', os.path.join(testkit.HOOKS, self.hook, 'hook.py'), '--config', self.config]
        procs = [subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) for _ in names]
        for proc, name in zip(procs, names):
            proc.stdin.write(json.dumps(self.read(self.memory(name))))
            proc.stdin.close()
        for proc in procs:
            proc.wait(timeout=30)
            proc.stdout.close()
        self.assertIsNone(self.run_hook(self.bash('ls')))

    def test_codex_reads_with_cat_and_other_commands_wait(self):
        out = self.run_hook(self.bash('git status'), dialect='codex')
        self.assertEqual(self.decision(out), 'deny')
        both = f"cat {self.memory('check-every-default.md')} {self.memory('one-format-inside.md')}"
        self.assertIsNone(self.run_hook(self.bash(both), dialect='codex'))
        self.assertEqual(self.decision(self.run_hook(self.bash(both + ' | head -3'), dialect='codex')), 'deny')
        self.run_hook(self.bash(both, phase='PostToolUse'), dialect='codex')
        self.assertIsNone(self.run_hook(self.bash('git status'), dialect='codex'))

    def test_claude_does_not_count_cat_unless_configured(self):
        both = f"cat {self.memory('check-every-default.md')} {self.memory('one-format-inside.md')}"
        self.assertEqual(self.decision(self.run_hook(self.bash(both))), 'deny')
        self.configure(shell_reads=True)
        self.assertIsNone(self.run_hook(self.bash(both)))
        self.run_hook(self.bash(both, phase='PostToolUse'))
        self.assertIsNone(self.run_hook(self.bash('ls')))


class FailsOpen(testkit.HookCase):
    hook = 'design-reading'

    def notice(self, r):
        self.assertEqual((r.returncode, r.stderr), (0, ''))
        out = json.loads(r.stdout)
        self.assertEqual(list(out), ['systemMessage'])
        return out['systemMessage']

    def test_a_missing_configuration_lets_the_action_through_and_says_so(self):
        r = self.run_raw(json.dumps(self.bash('ls')), config=os.path.join(self.tmp, 'absent.json'),
                         env={'XDG_STATE_HOME': os.path.join(self.tmp, 'xdg')})
        text = self.notice(r)
        self.assertIn('Hook design-reading could not run and let the action through: cannot read the configuration', text)
        with open(os.path.join(self.tmp, 'xdg', 'sparky-stereo-hooks', 'design-reading', 'errors.log')) as f:
            self.assertIn('HookError', f.read())

    def test_a_broken_configuration_lets_the_action_through_and_says_so(self):
        with open(self.config, 'w') as f:
            f.write('{"enabled": true,')
        text = self.notice(self.run_raw(json.dumps(self.bash('ls')), env={'XDG_STATE_HOME': os.path.join(self.tmp, 'xdg')}))
        self.assertIn('is not valid JSON', text)

    def test_an_event_that_is_not_json_lets_the_action_through_and_says_so(self):
        text = self.notice(self.run_raw('not json', env={'XDG_STATE_HOME': os.path.join(self.tmp, 'xdg')}))
        self.assertIn('JSONDecodeError', text)

    def test_an_error_inside_the_hook_is_logged_in_its_state_folder(self):
        self.configure(gap_seconds='soon')
        text = self.notice(self.run_raw(json.dumps(self.bash('ls'))))
        self.assertIn('ValueError', text)
        self.assertIn('ValueError', self.log('errors.log'))

    def test_no_workspace_is_said(self):
        with open(self.config) as f:
            cfg = json.load(f)
        del cfg['workspace']
        with open(self.config, 'w') as f:
            json.dump(cfg, f)
        text = self.notice(self.run_raw(json.dumps(self.bash('ls')), env={'XDG_STATE_HOME': os.path.join(self.tmp, 'xdg')}))
        self.assertIn('no workspace: set "workspace" in', text)

    def test_the_workspace_and_the_configuration_can_come_from_the_environment(self):
        r = self.run_raw(json.dumps(self.bash('ls')), args=[], env={'SPARKY_WORKSPACE': self.ws})
        self.assertEqual(self.decision(json.loads(r.stdout)), 'deny')
        r = self.run_raw(json.dumps(self.bash('ls')), args=[], env={'SPARKY_HOOKS_CONFIG_DIR': os.path.dirname(self.config)})
        self.assertEqual(self.decision(json.loads(r.stdout)), 'deny')


if __name__ == '__main__':
    unittest.main()
