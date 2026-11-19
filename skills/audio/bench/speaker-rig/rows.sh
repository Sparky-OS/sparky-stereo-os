#!/bin/bash
# rows.sh IMAGE [ROW...] : every proof row of case.py in a fresh rig container (one session per case), results to $SP_OUT/rows.jsonl.
# Needs DOCKER_HOST, SP_OUT, and SP_BUILD when the package under test is a build tree (DESTDIR) and not installed in the image.
# RETRY=1: a row that fails is run once more and both attempts are recorded ("attempt" 1 and 2): the rows measure samples a fake device
# writes at the wall clock, so on a machine whose load is above its cores a stream can underrun and cut a burst (1 s of noise
# arrives as 0.96 s); a real failure fails both times.
IMAGE=$1; shift
HERE=$(cd "$(dirname "$0")" && pwd)
ROWS=${*:-defaults level51 level71 distance51 distance71 bass51 bass71 testsignal51 testsignal71 refusal cards everyaccount everyaccount-refused leave late}
one() {
  r=$1; attempt=$2
  hide=; [ "$r" = refusal ] && hide=1
  late=; [ "$r" = late ] && late=1
  pk=; [ "$r" = everyaccount ] && pk=yes; [ "$r" = everyaccount-refused ] && pk=no
  SP_LATE=$late SP_POLKIT=$pk SP_HIDE_MODULE=$hide "$HERE/rig-run.sh" "row-$r" "$IMAGE" python3 -I /src/case.py "$r" 2>&1 | grep '^{' \
    | python3 -I -c "
import json,sys
for l in sys.stdin:
    d=json.loads(l); d['attempt']=$attempt; print(json.dumps(d))" | tee -a "${SP_OUT:?}/rows.jsonl" | python3 -I -c "
import json,sys
for l in sys.stdin:
    d=json.loads(l); print(('PASS' if d['ok'] else 'FAIL'), d['row'], sum(c['ok'] for c in d['checks']),'/',len(d['checks']), '(attempt %d)' % d['attempt'])
    for c in d['checks']:
        if not c['ok']: print('   FAILED:', c)"
  tail -1 "$SP_OUT/rows.jsonl" | python3 -I -c "import json,sys; sys.exit(0 if json.loads(sys.stdin.read())['ok'] else 1)"
}
for r in $ROWS; do
  one "$r" 1 || { [ -n "${RETRY:-}" ] && one "$r" 2; }
done
