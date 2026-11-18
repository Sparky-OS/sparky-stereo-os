#!/bin/sh
# run.sh GPU NAME WAIT CMD...  host side. GPU = llvmpipe | amd | nvidia
gpu=$1; name=$2; wait=$3; shift 3
W=${QB_WORK:?a folder for the cases}
case $gpu in
 llvmpipe) g="-e LIBGL_ALWAYS_SOFTWARE=1 -e GALLIUM_DRIVER=llvmpipe";;
 amd) g="--device /dev/dri/renderD128 --group-add 125";;
 nvidia) g="--device nvidia.com/gpu=0 --group-add 125 -e QB_SESSION_ENV=1 -e SPARKY_STEREO_OPENGL_CONF=/work/nv.conf -e SPARKY_STEREO_HARDWARE_LIB=/hw/usr/lib/sparky-stereo-hardware -e SPARKY_STEREO_HARDWARE_SHARE=/hw/usr/share/sparky/sparky-stereo-hardware --mount type=bind,src=$W/hw,dst=/hw,readonly";;
esac
rm -rf $W/h-$name; mkdir -p $W/h-$name; cp -a $W/home-tpl/. $W/h-$name/; docker rm -f qb-case >/dev/null 2>&1
docker run --rm --name qb-case --pull=never --ulimit core=0 --platform linux/amd64 --cpus 4 --user 1000:1000 \
 --cap-add SYS_NICE $g $QB_ENV \
 -e HOME=/work/h-$name \
 --mount type=bind,src=$W,dst=/work --mount type=bind,src=${QB_SCRIPTS:?the stereo-proof-rig scripts folder},dst=/scripts,readonly \
 --mount type=bind,src=$W/passwd,dst=/etc/passwd,readonly --mount type=bind,src=$W/group,dst=/etc/group,readonly \
 ${QB_IMAGE:?the rig image} sh -c 'cd /work/rig && gcc -O1 -o /tmp/qbtest qbtest.c -lGL -lX11 2>&1 | head -3; export PATH=/tmp:$PATH; ./case.sh /work/out/'$name' '$wait' "$@"' sh "$@"
