#!/bin/sh
# build-fakeinput.sh OUTDIR: inside the rig (wayland-scanner, a C compiler, libwayland-dev), build the fake input client into OUTDIR.
set -e
out=$1; here=$(cd "$(dirname "$0")" && pwd); mkdir -p "$out"; cd "$out"
wayland-scanner client-header "$here/fake-input.xml" fake-input-client-protocol.h
wayland-scanner private-code "$here/fake-input.xml" fake-input-protocol.c
cc -O2 -I. -o fakeinput "$here/fakeinput.c" fake-input-protocol.c -lwayland-client -lm
