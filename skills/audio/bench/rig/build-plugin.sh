#!/bin/sh
# Builds the fake device inside the rig image: build-plugin.sh OUTDIR
set -eu
gcc -O2 -Wall -fPIC -DPIC -shared "$(dirname "$0")/pcm_sa631.c" -o "$1/libasound_module_pcm_sa631.so" -lasound
