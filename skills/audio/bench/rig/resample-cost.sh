#!/bin/bash
# resample-cost.sh SRC_RATE DST_RATE SECONDS: processor time of PipeWire's own resampler (spa-resample) per quality 0..14
# for stereo float input. Prints: quality, cpu seconds, share of one core needed to resample in real time (cpu / seconds).
set -eu
src=$1 dst=$2 secs=$3
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
sox -n -b 32 -e floating-point -c 2 -r "$src" "$d/in.wav" synth "$secs" whitenoise vol 0.5
for q in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do
	t=$( { /usr/bin/time -f '%U %S' spa-resample -q "$q" -r "$dst" -f f32 "$d/in.wav" "$d/out.wav" >/dev/null; } 2>&1 | tail -1)
	echo "$q $t" | awk -v s="$secs" '{c=$2+$3; printf "q%-2d cpu %.3f s  share of a core in real time %.2f %%\n",$1,c,100*c/s}'
done
