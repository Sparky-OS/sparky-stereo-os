#!/bin/sh
# ffmpeg's own picture of a fixture's first frame at its sample aspect ratio (whole frame, scaled to square pixels)
# Usage: render-eye.sh FIXTURES OUTDIR NAME...
set -eu
F=$1 O=$2; shift 2
for n in "$@"; do
	ffmpeg -v error -y -i "$F/$n.mkv" -frames:v 1 -vf "scale=w='trunc(iw*sar/2)*2':h=ih:flags=neighbor,setsar=1" "$O/$n.png"
	echo "$n $(sha256sum "$O/$n.png" | cut -c1-16)"
done
