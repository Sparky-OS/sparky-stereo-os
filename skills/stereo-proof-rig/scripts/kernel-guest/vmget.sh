#!/bin/bash
# vmget.sh PORT REMOTE LOCAL   |   vmput.sh PORT LOCAL REMOTE (the same file, the other way)
V=${VMDIR:-$(cd "$(dirname "$0")" && pwd)}
O="-i $V/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
scp -q $O -P $1 root@127.0.0.1:"$2" "$3"
