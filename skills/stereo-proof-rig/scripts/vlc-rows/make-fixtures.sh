#!/bin/bash
# SPDX-License-Identifier: MIT
# the films of the proof, made inside the rig image with the edition's FFmpeg (x264 writes the frame packing SEI).
# 2D films: green with the same box. 3D films: LEFT eye red, RIGHT eye blue, a white box that moves, full side by side 1920x540 (two 960x540 eyes), SEI type 3.
# usage (inside the container): make-fixtures.sh OUTDIR
set -euo pipefail
o=${1:?out}; mkdir -p "$o"; cd "$o"
d=60
vid3d="color=c=red:s=960x540:r=24:d=$d[l];color=c=blue:s=960x540:r=24:d=$d[r];[l][r]hstack[bg];color=c=white:s=60x60:r=24:d=$d[b];[bg][b]overlay=x='mod(t*150,850)':y=200,format=yuv420p"
for k in 3d-silent 3d-sound; do
	a=(); [ $k = 3d-sound ] && a=(-f lavfi -i "sine=frequency=440:duration=$d" -c:a aac -b:a 96k)
	ffmpeg -v error -y -filter_complex "$vid3d" "${a[@]}" -c:v libx264 -preset veryfast -crf 20 -x264-params frame-packing=3 -shortest $k.mkv
done
vid2d="color=c=green:s=960x540:r=24:d=$d[bg];color=c=white:s=60x60:r=24:d=$d[b];[bg][b]overlay=x='mod(t*150,850)':y=200,format=yuv420p"
for k in 2d-silent 2d-sound; do
	a=(); [ $k = 2d-sound ] && a=(-f lavfi -i "sine=frequency=330:duration=$d" -c:a aac -b:a 96k)
	ffmpeg -v error -y -filter_complex "$vid2d" "${a[@]}" -c:v libx264 -preset veryfast -crf 20 -shortest $k.mkv
done
ffmpeg -v error -y -f lavfi -i "sine=frequency=550:duration=$d" -c:a aac -b:a 96k audio-only.m4a
ls -la
