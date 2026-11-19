#!/bin/bash
# rows.sh IMAGE [ROW...] : every proof row of case.py in a fresh rig container (one session per case), results to $SP_OUT/rows.jsonl
# Needs DOCKER_HOST, SP_OUT, and SP_BUILD when the package under test is a build tree (DESTDIR) and not installed in the image.
IMAGE=$1; shift
HERE=$(cd "$(dirname "$0")" && pwd)
ROWS=${*:-defaults level distance bass testsignal refusal stereo71 everyaccount everyaccount-refused}
for r in $ROWS; do
  hide=; [ "$r" = refusal ] && hide=1
  pk=; [ "$r" = everyaccount ] && pk=yes; [ "$r" = everyaccount-refused ] && pk=no
  SP_POLKIT=$pk SP_HIDE_MODULE=$hide "$HERE/rig-run.sh" "row-$r" "$IMAGE" python3 -I /src/case.py "$r" 2>&1 | grep '^{' | tee -a "${SP_OUT:?}/rows.jsonl" | python3 -I -c "
import json,sys
for l in sys.stdin:
    d=json.loads(l); print(('PASS' if d['ok'] else 'FAIL'), d['row'], sum(c['ok'] for c in d['checks']),'/',len(d['checks']))
    for c in d['checks']:
        if not c['ok']: print('   FAILED:', c)"
done
