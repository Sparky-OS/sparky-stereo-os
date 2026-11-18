#!/bin/bash
V=${VMDIR:-$(cd "$(dirname "$0")" && pwd)}
O="-i $V/id_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
scp -q -r $O -P $1 "$2" root@127.0.0.1:"$3"
