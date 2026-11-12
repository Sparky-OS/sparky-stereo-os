#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the disk-floors hook. Run: python3 hooks/tests/run.py disk-floors

A floor of 0 GiB is never crossed and a floor of a million GiB always is, so the tests need no particular disk.
"""
import json
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import testkit  # noqa: E402

HUGE = 1000000


class DiskFloors(testkit.HookCase):
    hook = 'disk-floors'

    def floors(self, **more):
        self.configure(floors_gib=None)
        return self.configure(floors_gib={self.ws: 0, **more})

    def test_init_wrote_real_folders_only(self):
        with open(self.config) as f:
            floors = json.load(f)['floors_gib']
        self.assertEqual(sorted(floors), sorted(['/', self.ws]))

    def test_above_the_floors_a_disk_shaped_command_gets_the_figures(self):
        self.floors()
        for command in ('df -h', 'cp -r build /tmp/copy', 'git clone https://example.org/x.git', 'docker pull debian:testing',
                        'tar -xf big.tar', 'rsync -a a/ b/', 'du -sh .'):
            with self.subTest(command):
                out = self.run_hook(self.bash(command))
                self.assertIsNone(self.decision(out))
                text = self.added_context(out)
                self.assertRegex(text, r'^Disk floors, GiB free, lowest first: ' + self.ws + r' \d+\.\d \(floor 0\)\.$')

    def test_other_commands_say_nothing_above_the_floors(self):
        self.floors()
        for command in ('ls -la', 'git status', 'python3 -m unittest', 'echo df', "cat > notes.md <<'EOF'\ncp -r a b\nEOF"):
            with self.subTest(command):
                self.assertIsNone(self.run_hook(self.bash(command)), command)

    def test_under_a_floor_every_command_is_told_once_per_interval(self):
        self.floors(**{self.tmp: HUGE})
        out = self.run_hook(self.bash('ls'))
        text = self.added_context(out)
        self.assertIn(f'{self.tmp} ', text)
        self.assertIn(f'UNDER its floor of {HUGE}', text)
        self.assertIn('Free what this work made', text)
        self.assertLess(text.index(self.tmp + ' '), text.index(self.ws + ' '))  # the folder under its floor comes first
        self.assertIsNone(self.run_hook(self.bash('ls')))            # told a moment ago
        self.assertIsNotNone(self.run_hook(self.bash('df -h')))      # asked: told again
        self.configure(remind_seconds=0)
        self.assertIsNotNone(self.run_hook(self.bash('ls')))

    def test_what_happens_to_a_write_under_a_floor_is_a_choice(self):
        self.floors(**{self.tmp: HUGE})
        write = 'cp -r build copy'
        self.assertIsNone(self.decision(self.run_hook(self.bash(write))))       # the default: told
        self.configure(below_floor='ask')
        self.assertEqual(self.decision(self.run_hook(self.bash(write))), 'ask')
        self.configure(below_floor='deny')
        out = self.run_hook(self.bash(write))
        self.assertEqual(self.decision(out), 'deny')
        self.assertIn('UNDER its floor', self.reason(out))
        self.assertIn('Free what this work made', self.reason(out))
        self.assertIn('cp -r build copy', self.log('refused.log'))
        # freeing space and looking are never refused
        for command in ('rm -rf build', 'df -h', 'docker rmi mine:1', 'ls'):
            with self.subTest(command):
                self.assertIsNone(self.decision(self.run_hook(self.bash(command))))

    def test_a_folder_that_cannot_be_measured_is_said(self):
        self.floors(**{os.path.join(self.tmp, 'absent'): 5})
        text = self.added_context(self.run_hook(self.bash('df -h')))
        self.assertIn('Not measured: ' + os.path.join(self.tmp, 'absent'), text)

    def test_no_floors_is_a_failure_that_is_said(self):
        self.configure(floors_gib=None)
        out = self.run_hook(self.bash('df -h'))
        self.assertIn('could not run and let the action through: no floors', out['systemMessage'])

    def test_switched_off_and_other_tools(self):
        self.floors(**{self.tmp: HUGE})
        self.assertIsNone(self.run_hook(self.event('PreToolUse', 'Write', {'file_path': '/x', 'content': 'df'})))
        self.configure(enabled=False)
        self.assertIsNone(self.run_hook(self.bash('df -h')))


if __name__ == '__main__':
    unittest.main()
