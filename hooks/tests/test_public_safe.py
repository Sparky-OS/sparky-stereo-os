#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Nothing of one person's machine in the hooks section: every path in it is an example or a configuration value.
Run: python3 hooks/tests/run.py public_safe"""
import json
import os
import re
import sys
import unittest

sys.dont_write_bytecode = True
HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HOOKS)
# a home folder that is not a placeholder, and mount points that only one machine has
LOCAL_PATH = re.compile(r'/home/(?!you\b|user\b|USER\b|\.\.\.)[A-Za-z0-9_.-]+/|/Users/(?!you\b|\.\.\.)[A-Za-z0-9_.-]+/|/(?:mnt|media|srv|opt)/[A-Za-z0-9_.-]+/')
ADDRESS = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+')
# not a person's contact: the domains reserved for examples, a forge's no-reply addresses, the ssh user of a remote, file names
RESERVED = re.compile(r'(?i)^git@|@(?:[\w.-]+\.)?example\.(?:org|com|net)$|\.(?:example|invalid|test)$|@users\.noreply\.github\.com$|@2x\.png$|@tty1\.service$')


def files():
    folders = [HOOKS, os.path.join(REPO, 'skills', 'making-skills'), os.path.join(REPO, 'skills', 'development-hooks'),
               os.path.join(REPO, 'tools', 'tests')]
    for folder in folders:
        for base, dirs, names in os.walk(folder):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for name in names:
                yield os.path.join(base, name)


class PublicSafe(unittest.TestCase):
    def test_no_path_of_one_machine_and_no_person_s_address(self):
        found = []
        for path in files():
            with open(path, encoding='utf-8', errors='replace') as f:
                for n, line in enumerate(f, 1):
                    if LOCAL_PATH.search(line):
                        found.append(f'{os.path.relpath(path, REPO)}:{n}: a path of one machine: {line.strip()[:90]}')
                    for address in ADDRESS.findall(line):
                        if not RESERVED.search(address) and '://' not in line:
                            found.append(f'{os.path.relpath(path, REPO)}:{n}: an address: {address}')
        self.assertEqual(found, [])

    def test_every_example_configuration_is_generic(self):
        for name in sorted(os.listdir(HOOKS)):
            example = os.path.join(HOOKS, name, 'config.example.json')
            if not os.path.isfile(example):
                continue
            with self.subTest(name):
                with open(example) as f:
                    cfg = json.load(f)
                self.assertEqual(cfg['workspace'], '/path/to/your/workspace')
                for key, value in (cfg.get('paths') or {}).items():
                    self.assertFalse(os.path.isabs(value), f'{name}: paths.{key} is absolute')

    def test_the_section_passes_its_own_publish_check_with_the_example_configuration(self):
        import subprocess
        checked = [p for p in files() if not p.endswith(('vocab.txt', 'window-goldens.tsv', 'char-classes.txt'))]
        checked += [os.path.join(REPO, 'tools', 'check-skills.py'), os.path.join(REPO, 'tools', 'skill-window', 'wordpiece.py'),
                    os.path.join(REPO, 'tools', 'skill-window', 'regenerate.py'), os.path.join(REPO, 'tools', 'skill-window', 'README.md')]
        r = subprocess.run([sys.executable, '-B', os.path.join(HOOKS, 'publish-check', 'publish_check.py'), '--config',
                            os.path.join(HOOKS, 'publish-check', 'config.example.json'), '--files', *checked], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, 'publish-check: clean\n', ''))
        self.assertGreater(len(checked), 50)

    def test_no_bytecode_and_no_state_is_left_in_the_section(self):
        left = [p for p in files() if p.endswith(('.pyc', '.log', '.lock')) or '/state/' in p]
        self.assertEqual(left, [])


if __name__ == '__main__':
    unittest.main()
