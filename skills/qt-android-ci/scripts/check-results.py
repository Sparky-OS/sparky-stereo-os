# SPDX-License-Identifier: GPL-2.0-or-later
import sys
import re
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('Usage: check-results.py QTEST_LOG RUNNER_EXIT_FILE')
output = Path(sys.argv[1]).read_text()
exit_file = Path(sys.argv[2])
expected = [
    'initTestCase()', 'testMediaFilesAreSupported()',
    *[f'maxLuminance_isTheMasteringDisplaysPeakInNits({row})'
      for row in ('one_red_frame', 'colors', 'mastering_1000nits')],
    *[f'toImage_retainsThePreviousMappedState({frame}.{mode})'
      for frame in ('defaulFrame', 'mediaPlayerFrame') for mode in ('notMapped', 'readOnly')],
    *[f'toImage_rendersUpdatedFrame_afterMappingInWriteModeAndModifying({frame}.{mode})'
      for frame in ('defaulFrame', 'mediaPlayerFrame') for mode in ('writeOnly', 'readWrite')],
    'toImage_returnsImage_whenCalledFromSeparateThreadAndWhileRenderingToWindow(OpenGL)',
    'cleanupTestCase()',
]
actual = re.findall(r'^PASS\s+: tst_QVideoFrameBackend::(.+)$', output, re.MULTILINE)
assert actual == expected, (actual, expected)
assert not re.search(r'^(SKIP|FAIL!|QFATAL)', output, re.MULTILINE)
assert 'Totals: 15 passed, 0 failed, 0 skipped, 0 blacklisted' in output
assert 'Using Qt multimedia with FFmpeg version 9.0.2 LGPL version 2.1 or later' in output
assert 'x86_64-little_endian-lp64' in output and 'android 9.0' in output
assert exit_file.read_text().strip() == '0'
for test in actual:
    print(f'PASS {test}')
print('Verified: all 15 expected results passed, no skips, runner exit 0.')
