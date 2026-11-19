#!/bin/sh
# run.sh NAME PROGRAM-ARGS...  (host side): one fresh container and session per case; env passes through (WAIT, TD, W, H)
: "${DOCKER_HOST:?set DOCKER_HOST}"
name=$1; steps=$2; shift 2
docker rm -f stereo-guide-case >/dev/null 2>&1
docker run --rm --name stereo-guide-case --pull=never --ulimit core=0 --network none --cap-add SYS_NICE --cpus 4 --user 1000:1000 --device /dev/dri/renderD128 --group-add 125 \
 -e HOME=/out/home-$name -e WAIT -e TD -e XW -e W -e H -e LANG=en_US.UTF-8 \
 --mount type=bind,src=${WORK:?set WORK}/cap,dst=/out \
 --mount type=bind,src=${WORK:?set WORK}/steps,dst=/steps,readonly --mount type=bind,src=${WORK:?set WORK}/fx,dst=/fx,readonly \
 --mount type=bind,src=${WORK:?set WORK}/tools,dst=/tools,readonly \
 --mount type=bind,src=${SKILLS:?set SKILLS}/stereo-proof-rig/scripts,dst=/scripts,readonly \
 ${RIG_IMAGE:?set RIG_IMAGE} sh -c 'mkdir -p $HOME; dbus-run-session -- /tools/case.sh /out "$@"' sh "$name" "$steps" "$@"
