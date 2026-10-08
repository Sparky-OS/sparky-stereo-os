#!/bin/sh
# The LEFT/RIGHT side by side (half) test clip in an mpv window, looping
. "$(dirname "$0")/session.env"
exec mpv --loop=inf --geometry=960x540 --no-terminal /tmp/sbs-half-1080p24-sei-60s.mp4
