#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of install.py: the default layout, the configurations, the wiring for a tool and its removal.
Run: python3 hooks/tests/run.py install"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HOOKS)
sys.path.insert(0, os.path.join(HOOKS, 'lib'))
import install  # noqa: E402

ALL = ['brief-and-handback', 'container-guard', 'design-reading', 'disk-floors', 'outreach-guard', 'publish-check', 'stereo-contract-guard']


def run(*args):
    return subprocess.run([sys.executable, '-B', os.path.join(HOOKS, 'install.py'), *args], capture_output=True, text=True)


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='install-test-')
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.ws = os.path.join(self.tmp, 'work space')  # a space in the path, on purpose

    def config(self, name):
        with open(install.config_path(self.ws, name)) as f:
            return json.load(f)

    def configure(self, name, **changes):
        cfg = self.config(name)
        for key, value in changes.items():
            if isinstance(value, dict) and isinstance(cfg.get(key), dict):
                cfg[key].update(value)
            else:
                cfg[key] = value
        with open(install.config_path(self.ws, name), 'w') as f:
            json.dump(cfg, f)

    def test_every_hook_folder_is_whole(self):
        self.assertEqual(install.hook_names(), ALL)
        for name in ALL:
            for part in ('hook.py', 'config.example.json', 'wiring.json', 'README.md'):
                with self.subTest(f'{name}/{part}'):
                    self.assertTrue(os.path.isfile(os.path.join(HOOKS, name, part)))
            self.assertTrue(any(n.startswith('test_') for n in os.listdir(os.path.join(HOOKS, name, 'tests'))), name)
            with open(os.path.join(HOOKS, name, 'config.example.json')) as f:
                example = json.load(f)
            self.assertIs(example['enabled'], True, name)                       # the edition's defaults are on
            self.assertEqual(example['workspace'], install.PLACEHOLDER_WORKSPACE, name)

    def test_init_makes_the_default_layout_and_one_configuration_per_hook(self):
        r = run('init', self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        for folder in ('memory', 'repos', 'partners/queue', 'private/drafts', 'private/hooks', 'state/hooks'):
            self.assertTrue(os.path.isdir(os.path.join(self.ws, folder)), folder)
        for starter in ('memory/MEMORY.md', 'partners/HOUSE-RULES.md', 'private/README.md', 'private/ledger.md'):
            self.assertTrue(os.path.isfile(os.path.join(self.ws, starter)), starter)
        self.assertEqual(os.stat(os.path.join(self.ws, 'private')).st_mode & 0o777, 0o700)
        for name in ALL:
            cfg = self.config(name)
            self.assertEqual(cfg['workspace'], self.ws)
            self.assertEqual(os.stat(install.config_path(self.ws, name)).st_mode & 0o777, 0o600)
            self.assertNotIn('/path/to/your', json.dumps(cfg))
        # this checkout is not under WORKSPACE/repos, so the configurations name where its skills are
        self.assertEqual(self.config('outreach-guard')['paths']['skills'], os.path.join(os.path.dirname(HOOKS), 'skills'))
        self.assertEqual(sorted(self.config('disk-floors')['floors_gib']), sorted(['/', self.ws]))

    def test_init_keeps_what_exists(self):
        run('init', self.ws)
        path = install.config_path(self.ws, 'design-reading')
        cfg = self.config('design-reading')
        cfg['core'] = ['my-own.md']
        with open(path, 'w') as f:
            json.dump(cfg, f)
        with open(os.path.join(self.ws, 'memory', 'MEMORY.md'), 'w') as f:
            f.write('# mine\n')
        r = run('init', self.ws, '--scratch', os.path.join(self.tmp, 'scratch'))
        self.assertIn(f'kept   {path}', r.stdout)
        self.assertEqual(self.config('design-reading')['core'], ['my-own.md'])
        with open(os.path.join(self.ws, 'memory', 'MEMORY.md')) as f:
            self.assertEqual(f.read(), '# mine\n')

    def test_a_scratch_folder_gets_its_floor(self):
        scratch = os.path.join(self.tmp, 'scratch')
        os.mkdir(scratch)
        run('init', self.ws, '--scratch', scratch)
        self.assertEqual(self.config('disk-floors')['floors_gib'][scratch], 2)

    def test_paths_with_json_characters_survive_init_and_wiring(self):
        self.ws = os.path.join(self.tmp, 'work "quoted" \\ name')
        scratch = os.path.join(self.tmp, 'scratch "quoted" \\ name')
        os.mkdir(scratch)
        result = run('init', self.ws, '--scratch', scratch)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ALL:
            self.assertEqual(self.config(name)['workspace'], self.ws)
        self.assertEqual(self.config('disk-floors')['floors_gib'][scratch], 2)
        command = install.command_for('design-reading', self.ws, 'claude')
        result = subprocess.run(command, shell=True, input='{}', capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stderr, result.stdout), (0, '', ''))

    def test_each_settings_write_keeps_its_own_backup(self):
        settings = os.path.join(self.tmp, 'settings.json')
        with open(settings, 'w') as f:
            json.dump({'version': 0}, f)
        with mock.patch.object(install.time, 'strftime', return_value='same-second'):
            for version in (1, 2):
                install.write_settings(settings, {'version': version}, say=lambda line: None)
        copies = [n for n in os.listdir(self.tmp) if n.startswith('settings.json.before-hooks-')]
        self.assertEqual(len(copies), 2)
        versions = []
        for copy in copies:
            with open(os.path.join(self.tmp, copy)) as f:
                versions.append(json.load(f)['version'])
        self.assertEqual(sorted(versions), [0, 1])

    def test_check_names_what_is_missing_and_passes_when_nothing_is(self):
        run('init', self.ws)
        r = run('check', self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn('design-reading: on; first_call on, gap on, lane_named on, session_start on', r.stdout)
        self.assertIn('core file not found: ' + os.path.join(self.ws, 'memory', 'check-every-default.md'), r.stdout)
        self.assertIn('always_read file not found: ' + os.path.join(self.ws, 'memory', 'how-we-write-upstream.md'), r.stdout)
        self.assertNotIn('upstream-outreach', r.stdout)   # found in this checkout's skills, through "skills:"
        for name in ('check-every-default.md', 'one-format-inside.md', 'how-we-write-upstream.md'):
            with open(os.path.join(self.ws, 'memory', name), 'w') as f:
                f.write('A fact.\n')
        r = run('check', self.ws)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn('Every configuration reads, and every file it names exists.', r.stdout)
        self.configure('design-reading', core=[])
        r = run('check', self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn('"core" names no file, so nothing is required reading', r.stdout)
        self.configure('design-reading', on={'session_start': False, 'first_call': False, 'gap': False})
        self.assertEqual(run('check', self.ws).returncode, 0)
        with open(install.config_path(self.ws, 'disk-floors'), 'w') as f:
            f.write('{nope')
        r = run('check', self.ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn('disk-floors: NOT USABLE', r.stdout)

    def test_the_wiring_for_claude_code(self):
        run('init', self.ws)
        r = run('wire', 'claude', self.ws)
        self.assertEqual(r.returncode, 0, r.stderr)
        hooks = json.loads(r.stdout)['hooks']
        self.assertEqual(sorted(hooks), ['PostToolUse', 'PreToolUse', 'SessionStart', 'UserPromptSubmit'])
        by_matcher = {g.get('matcher'): [h['command'] for h in g['hooks']] for g in hooks['PreToolUse']}
        self.assertEqual(sorted(by_matcher), ['*', 'Agent|Task|SubagentHandback', 'Bash', 'Edit|Write'])
        bash = ' '.join(by_matcher['Bash'])
        for name in ('container-guard', 'disk-floors', 'outreach-guard', 'publish-check', 'stereo-contract-guard'):
            self.assertIn(f'/{name}/hook.py', bash)
        self.assertNotIn('design-reading', bash)       # it is wired once, on every tool
        command = by_matcher['*'][0]
        self.assertEqual(command, f"python3 {HOOKS}/design-reading/hook.py --config '{self.ws}/private/hooks/design-reading.json'")
        self.assertNotIn('matcher', hooks['UserPromptSubmit'][0])
        post = {g['matcher'] for g in hooks['PostToolUse']}
        self.assertEqual(post, {'Read', 'mcp__reference__consult_knowledge'})
        self.assertTrue(all(h['type'] == 'command' and h['timeout'] > 0 for g in hooks['PreToolUse'] for h in g['hooks']))

    def test_the_wiring_runs(self):
        """The commands of the wiring are run as a shell runs them, with an event on stdin."""
        run('init', self.ws)
        hooks = json.loads(run('wire', 'claude', self.ws).stdout)['hooks']
        event = {'session_id': 's', 'transcript_path': '/t.jsonl', 'cwd': self.ws, 'hook_event_name': 'PreToolUse',
                 'tool_name': 'Bash', 'tool_input': {'command': 'ls'}}
        for group in hooks['PreToolUse']:
            for handler in group['hooks']:
                with self.subTest(handler['command']):
                    r = subprocess.run(handler['command'], shell=True, input=json.dumps(event), capture_output=True, text=True)
                    self.assertEqual((r.returncode, r.stderr), (0, ''))
                    self.assertNotIn('could not run', r.stdout)

    def test_only_some_hooks_and_the_failure_choice(self):
        run('init', self.ws)
        r = run('wire', 'claude', self.ws, '--only', 'disk-floors,container-guard', '--on-failure', 'block')
        hooks = json.loads(r.stdout)['hooks']
        self.assertEqual(list(hooks), ['PreToolUse'])
        handlers = hooks['PreToolUse'][0]['hooks']
        self.assertEqual(len(handlers), 2)
        self.assertTrue(all(h['onFailure'] == 'block' for h in handlers))
        r = run('wire', 'claude', self.ws, '--only', 'no-such-hook')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('no such hook: no-such-hook', r.stderr)

    def test_the_wiring_for_codex_names_its_dialect_and_its_tools(self):
        run('init', self.ws)
        hooks = json.loads(run('wire', 'codex', self.ws).stdout)['hooks']
        commands = [h['command'] for groups in hooks.values() for g in groups for h in g['hooks']]
        self.assertTrue(all(c.endswith('--dialect codex') for c in commands))
        self.assertIn('apply_patch', {g.get('matcher') for g in hooks['PreToolUse']})
        self.assertNotIn('Read', {g.get('matcher') for g in hooks['PostToolUse']})

    def test_wiring_without_a_configuration_stops_and_says_which(self):
        r = run('wire', 'claude', self.ws)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('cannot read the configuration', r.stderr)

    def test_write_merges_keeps_a_copy_and_unwire_takes_only_ours_out(self):
        run('init', self.ws)
        settings = os.path.join(self.tmp, 'settings.json')
        theirs = {'permissions': {'allow': ['Bash(ls:*)']},
                  'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'python3 /somewhere/else/guard.py'}]}],
                            'Stop': [{'hooks': [{'type': 'command', 'command': 'notify-done'}]}]}}
        with open(settings, 'w') as f:
            json.dump(theirs, f)
        r = run('wire', 'claude', self.ws, '--write', settings)
        self.assertEqual(r.returncode, 0, r.stderr)
        copies = [n for n in os.listdir(self.tmp) if n.startswith('settings.json.before-hooks-')]
        self.assertEqual(len(copies), 1)
        with open(os.path.join(self.tmp, copies[0])) as f:
            self.assertEqual(json.load(f), theirs)
        with open(settings) as f:
            merged = json.load(f)
        self.assertEqual(merged['permissions'], theirs['permissions'])
        self.assertEqual(merged['hooks']['Stop'], theirs['hooks']['Stop'])
        commands = [h['command'] for g in merged['hooks']['PreToolUse'] for h in g['hooks']]
        self.assertIn('python3 /somewhere/else/guard.py', commands)
        ours = [c for c in commands if HOOKS in c]
        self.assertEqual(len(ours), 9)
        # writing again replaces our entries instead of adding them twice
        run('wire', 'claude', self.ws, '--write', settings)
        with open(settings) as f:
            again = json.load(f)
        self.assertEqual(len([h for g in again['hooks']['PreToolUse'] for h in g['hooks'] if HOOKS in h['command']]), 9)
        r = run('unwire', settings)
        self.assertIn('handler(s) of', r.stdout)
        with open(settings) as f:
            self.assertEqual(json.load(f), theirs)

    def test_write_makes_a_new_file_when_there_is_none(self):
        run('init', self.ws)
        settings = os.path.join(self.tmp, 'new', 'settings.json')
        self.assertEqual(run('wire', 'claude', self.ws, '--write', settings).returncode, 0)
        with open(settings) as f:
            self.assertIn('PreToolUse', json.load(f)['hooks'])

    def test_the_git_commands_are_printed_not_run(self):
        run('init', self.ws)
        r = run('git', os.path.join(self.tmp, 'some repo'), self.ws)
        self.assertEqual(r.returncode, 0)
        self.assertIn(f"config core.hooksPath {HOOKS}/publish-check/git", r.stdout)
        self.assertIn("config sparky.publishCheckConfig", r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, 'some repo')))


if __name__ == '__main__':
    unittest.main()
