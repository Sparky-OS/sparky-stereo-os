#!/bin/bash
# vmroot.sh PORT 'commands': run them in the guest as root. (A script goes in through stdin, so no quoting layer of ssh and runuser reaches it.)
P=$1; V=${VMDIR:-$(cd "$(dirname "$0")" && pwd)}
O="-i $V/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 -o LogLevel=ERROR"
printf '%s\n' "$2" | ssh $O -p $P root@127.0.0.1 'cat >/tmp/rootcmd.sh; bash /tmp/rootcmd.sh'
