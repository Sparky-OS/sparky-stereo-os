#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the container-guard hook. Run: python3 hooks/tests/run.py container-guard

The engine's name is put into each command while the test runs, so that this file can be written on a machine
where a guard of this kind is already on duty.
"""
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

D = 'dock' + 'er'
P = 'pod' + 'man'


class ContainerGuard(testkit.HookCase):
    hook = 'container-guard'

    def test_an_action_on_an_unfiltered_list_is_refused(self):
        for command in (f'{D} kill $({D} ps -q)', f'{D} rm -f $({D} ps -aq)', f'{D} stop `{D} ps -q`',
                        f'{D} ps -q | xargs {D} stop', f'{D} ps -q | while read c; do {D} kill $c; done',
                        f'{D} container stop $({D} container ls -q)', f'{P} rm -f $({P} ps -aq)',
                        f'for c in $({D} ps -q); do {D} restart $c; done'):
            with self.subTest(command):
                out = self.run_hook(self.bash(command))
                self.assertEqual(self.decision(out), 'deny')
                self.assertIn('every container of the shared daemon', self.reason(out))
                self.assertIn('--filter name=YOUR_PREFIX', self.reason(out))
        self.assertIn('kill', self.log('refused.log'))

    def test_a_filtered_list_and_named_containers_pass(self):
        for command in (f'{D} kill $({D} ps -q --filter name=lane-7-)', f'{D} ps -q -f name=mine | xargs {D} stop',
                        f'{D} rm -f lane-7-build lane-7-test', f'{D} stop lane-7-rig', f'{D} ps -a', f'{D} ps -q | wc -l',
                        f'{D} run --rm --name lane-7-x debian:testing true', f'{D} logs $({D} ps -q)'):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)), command)

    def test_a_protected_service_is_never_acted_on(self):
        for command in (f'{D} stop reference-index', f'{D} rm -f registry-mirror', f'{D} restart lane-7-x reference-index',
                        f'{D} kill --signal KILL reference-index'):
            with self.subTest(command):
                out = self.run_hook(self.bash(command))
                self.assertEqual(self.decision(out), 'deny')
                self.assertIn('a service that stays running on this machine (reference-index, registry-mirror)', self.reason(out))
        for command in (f'{D} logs reference-index', f'{D} inspect registry-mirror', f'{D} stop my-reference-index-test',
                        f'{D} stop lane-7-x; curl http://reference-index:6333/'):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)), command)

    def test_a_prune_of_everything_is_refused_only_when_switched_on(self):
        for command in (f'{D} system prune -af', f'{D} image prune -a', f'{D} builder prune'):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)))
        self.configure(refuse_global_prune=True)
        out = self.run_hook(self.bash(f'{D} system prune -af'))
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn('Remove your own images and containers by name', self.reason(out))
        self.assertIsNone(self.run_hook(self.bash(f'{D} image prune --filter label=lane=7')))

    def test_text_that_is_only_written_is_not_a_command(self):
        heredoc = f"cat > cleanup-notes.md <<'EOF'\nNever run: {D} kill $({D} ps -q)\nEOF"
        self.assertIsNone(self.run_hook(self.bash(heredoc)))
        handed = f"bash <<'EOF'\n{D} kill $({D} ps -q)\nEOF"
        self.assertEqual(self.decision(self.run_hook(self.bash(handed))), 'deny')

    def test_switches(self):
        self.configure(refuse_unfiltered_lists=False, protected=[])
        self.assertIsNone(self.run_hook(self.bash(f'{D} kill $({D} ps -q)')))
        self.assertIsNone(self.run_hook(self.bash(f'{D} stop reference-index')))
        self.configure(refuse_unfiltered_lists=True, enabled=False)
        self.assertIsNone(self.run_hook(self.bash(f'{D} kill $({D} ps -q)')))

    def test_a_guard_that_keeps_no_state_does_not_wait_for_another_run(self):
        with self.state_lock_held():
            out = self.run_hook(self.bash(f'{D} kill $({D} ps -q)'))
        self.assertEqual(self.decision(out), 'deny')
        self.assertEqual(self.log('errors.log'), '')


if __name__ == '__main__':
    unittest.main()
