#!/bin/bash
# rig-run.sh NAME IMAGE COMMAND... : one rig container per case, removed when it ends. As root it prepares the run folders and a
# systemctl that restarts the private session the way systemd would, then runs COMMAND as the user "rig" inside the session.
# Needs DOCKER_HOST (the lane's socket), SP_OUT (a world-writable scratch folder, /ev inside) and optional SP_MOUNTS (more -v).
set -u
NAME=$1 IMAGE=$2; shift 2
HERE=$(cd "$(dirname "$0")" && pwd)
docker rm -f "sp23-$NAME" >/dev/null 2>&1
docker run --rm --name "sp23-$NAME" -e SP_HIDE_MODULE="${SP_HIDE_MODULE:-}" -e SP_POLKIT="${SP_POLKIT:-}" -e SP_LATE="${SP_LATE:-}" -e SP_BARE="${SP_BARE:-}" -e SP_LANG="${SP_LANG:-}" -e SP_LANGUAGE="${SP_LANGUAGE:-}" -e SP_SCALE="${SP_SCALE:-}" --pull=never --network none --ulimit core=0 --cpus 2 ${SP_MOUNTS:-} \
  -v "$HERE":/src:ro ${SP_BUILD:+-v $SP_BUILD:/build:ro} -v "${SP_OUT:?}":/ev "$IMAGE" bash /src/rig-inner.sh "$@"
