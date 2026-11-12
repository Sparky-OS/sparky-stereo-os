#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run the hooks' tests: every hook's own, and the shared ones in this folder.

  python3 hooks/tests/run.py              all of them
  python3 hooks/tests/run.py NAME...      only the hooks or test files whose name holds one of these words
  python3 hooks/tests/run.py -v           one line per test

They need python3 and git; the publish check's picture test also uses exiftool when it is installed and says so
when it is not. No network, no model, no AI tool: each test pipes an event into a hook and reads the answer.
Exit status: 0 when every test passed, 1 otherwise.
"""
import glob
import os
import sys
import unittest

sys.dont_write_bytecode = True
HOOKS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    verbose = '-v' in argv
    words = [a for a in argv if not a.startswith('-')]
    files = sorted(glob.glob(os.path.join(HOOKS, '*', 'tests', 'test_*.py')) + glob.glob(os.path.join(HOOKS, 'tests', 'test_*.py')))
    if words:
        files = [f for f in files if any(w in os.path.relpath(f, HOOKS) for w in words)]
    if not files:
        print(f'run.py: no test file matches {" ".join(words)}', file=sys.stderr)
        return 1
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for path in files:
        folder = os.path.dirname(path)
        sys.path.insert(0, folder)
        suite.addTests(loader.discover(folder, pattern=os.path.basename(path), top_level_dir=folder))
        sys.path.pop(0)
    result = unittest.TextTestRunner(verbosity=2 if verbose else 1).run(suite)
    print(f'{len(files)} test files, {result.testsRun} tests: '
          + ('all passed' if result.wasSuccessful() else f'{len(result.failures)} failed, {len(result.errors)} errors')
          + (f', {len(result.skipped)} skipped ({"; ".join(reason for _, reason in result.skipped)})' if result.skipped else ''))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
