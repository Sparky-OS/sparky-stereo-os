#!/bin/sh
# Root part of the throwaway container: a passwd entry for uid 1000 (D-Bus refuses a uid without one), then
# scenario.sh as that uid. The environment (RIG, WORK, QT_PREFIX, PROBE, EVIDENCE) passes through.
# Usage: entry.sh NAME BUILD (SCENARIO=replug.sh for case 10)
set -eu
echo "rig:x:1000:1000::/tmp:/bin/sh" >> /etc/passwd
echo "rig:x:1000:" >> /etc/group
exec setpriv --reuid=1000 --regid=1000 --clear-groups bash "$RIG/${SCENARIO:-scenario.sh}" "$@"
