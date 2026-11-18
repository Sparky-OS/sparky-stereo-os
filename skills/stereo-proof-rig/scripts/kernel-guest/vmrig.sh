#!/bin/bash
# vmrig.sh PORT 'commands': run them in the guest as the session user `rig` with the Plasma session's environment (~/env.sh) loaded.
P=$1; V=${VMDIR:-$(cd "$(dirname "$0")" && pwd)}
O="-i $V/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 -o LogLevel=ERROR"
printf '. /home/rig/env.sh\n%s\n' "$2" | ssh $O -p $P root@127.0.0.1 'cat >/tmp/rigcmd.sh; chmod 644 /tmp/rigcmd.sh; runuser -u rig -- bash /tmp/rigcmd.sh'
