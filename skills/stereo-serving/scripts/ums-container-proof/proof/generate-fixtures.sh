#!/bin/sh
# One second of video per fixture: the left view solid red, the right view solid cyan,
# the container's stereo_mode tag set for the packing under test.
# Run inside the controller image (FFmpeg with libx264); usage: generate-fixtures.sh MEDIA_DIR PROBE_DIR
set -eu
output=${1:?media directory}
probes=${2:?probe directory}
mkdir -p "$output" "$probes"

# name, stereo_mode tag (none for 2D), pixel format, filter graph that ends in [out]
make_fixture() {
  name=$1
  stereo_mode=$2
  pix_fmt=$3
  filter=$4
  tag=""
  if [ "$stereo_mode" != none ]; then
    tag="-metadata:s:v:0 stereo_mode=$stereo_mode"
  fi
  # shellcheck disable=SC2086
  ffmpeg -hide_banner -loglevel error -y -filter_complex "$filter" -map "[out]" -t "${DURATION:-1}" \
    -c:v libx264 -crf 12 -pix_fmt "$pix_fmt" ${KEYINT:+-g $KEYINT} -an $tag "$output/$name.mkv"
}

eyes() { # width height rate
  echo "color=red:size=$1x$2:rate=$3[left];color=cyan:size=$1x$2:rate=$3[right]"
}

# Packings that keep each eye whole and apart (4:2:0 is enough)
make_fixture full-sbs-left left_right yuv420p \
  "$(eyes 960 1080 25);[left][right]hstack[out]"
make_fixture half-sbs left_right yuv420p \
  "$(eyes 960 540 25);[left][right]hstack[out]"
make_fixture top-bottom top_bottom yuv420p \
  "$(eyes 1920 540 25);[left][right]vstack[out]"
make_fixture right-first right_left yuv420p \
  "color=cyan:size=960x1080:rate=25[left];color=red:size=960x1080:rate=25[right];[left][right]hstack[out]"
make_fixture mono-left none yuv420p \
  "color=red:size=1920x1080:rate=25[out]"

# Interleaved packings mix the eyes inside a 2x2 chroma block, so they need 4:4:4
# (H.264 D.2.26 Table D-9 values 0, 1 and 2; Matroska StereoMode 4 to 9, RFC 9559)
make_fixture rows-first-left row_interleaved_lr yuv444p \
  "$(eyes 1920 540 25);[left][right]vstack,stereo3d=abl:irl[out]"
make_fixture rows-first-right row_interleaved_rl yuv444p \
  "$(eyes 1920 540 25);[left][right]vstack,stereo3d=abl:irr[out]"
make_fixture columns-first-left col_interleaved_lr yuv444p \
  "$(eyes 960 1080 25);[left][right]hstack,stereo3d=sbsl:icl[out]"
make_fixture columns-first-right col_interleaved_rl yuv444p \
  "$(eyes 960 1080 25);[left][right]hstack,stereo3d=sbsl:icr[out]"
make_fixture checker-first-left checkerboard_lr yuv444p \
  "$(eyes 960 1080 25);[left][right]hstack,stereo3d=sbsl:chl[out]"
make_fixture checker-first-right checkerboard_rl yuv444p \
  "$(eyes 960 1080 25);[left][right]hstack,stereo3d=sbsl:chr[out]"

# Alternating frames: 1 s of picture pairs, so 50 frames of 1280x720 (Matroska StereoMode 13 and 14)
make_fixture frames-first-left block_lr yuv420p \
  "$(eyes 1280 720 25);[left][right]hstack,stereo3d=sbsl:al[out]"
make_fixture frames-first-right block_rl yuv420p \
  "$(eyes 1280 720 25);[left][right]hstack,stereo3d=sbsl:ar[out]"

# A layout UMS cannot convert: the control that must stay refused, with its warning
make_fixture anaglyph-cyan-red anaglyph_cyan_red yuv420p \
  "$(eyes 1920 1080 25);[left][right]hstack,stereo3d=sbsl:arcd,scale=1920:1080[out]"

# The frame packing SEI in the stream and nothing in the container (H.264 D.2.26: 3 side by side, 4 top and bottom)
ffmpeg -hide_banner -loglevel error -y -filter_complex "$(eyes 960 1080 25);[left][right]hstack[out]" -map "[out]" -t 1 \
  -c:v libx264 -crf 12 -x264-params "frame-packing=3" -pix_fmt yuv420p -an "$output/sei-sbs-left.mkv"
ffmpeg -hide_banner -loglevel error -y -filter_complex "$(eyes 1920 540 25);[left][right]vstack[out]" -map "[out]" -t 1 \
  -c:v libx264 -crf 12 -x264-params "frame-packing=4" -pix_fmt yuv420p -an "$output/sei-tb-left.mkv"

# Eight seconds, the left view red for four and green after, a keyframe every second: a seek by the picture,
# also where UMS copies the video and the player can only start at a keyframe
DURATION=8 KEYINT=25 make_fixture seek-sbs left_right yuv420p \
  "color=red:size=960x1080:rate=25:duration=4[a];color=lime:size=960x1080:rate=25:duration=4[b];[a][b]concat=n=2:v=1:a=0[left];color=cyan:size=960x1080:rate=25:duration=8[right];[left][right]hstack[out]"

for fixture in "$output"/*.mkv; do
  ffprobe -v error -select_streams v:0 -show_streams -of json "$fixture" > "$probes/$(basename "$fixture").probe.json"
done
