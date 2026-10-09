#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Runs ./bench inside the tool image (Dockerfile), as the current user, with KVM if the host has it.
#
#   ./run-in-docker.sh [-m HOSTDIR:CONTAINERDIR]... bench-arguments...
#
# The image is built on first use. The directory of this script is mounted at /bench (read-only) and ./bench-work
# at /work. Mount the kernel image and any root file system at the same path they have on the host, e.g.
#   ./run-in-docker.sh -m $HOME/build/vkms:$HOME/build/vkms:ro --kernel $HOME/build/vkms/arch/x86/boot/bzImage run all
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
IMAGE=${BENCH_IMAGE:-vkms-stereo-bench:1}
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker build --platform linux/amd64 -t "$IMAGE" "$HERE"
mkdir -p "$PWD/bench-work"
MOUNTS=
while [ "${1:-}" = "-m" ]; do MOUNTS="$MOUNTS -v $2"; shift 2; done
KVM=
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then KVM="--device /dev/kvm --group-add $(getent group kvm | cut -d: -f3)"; fi
# shellcheck disable=SC2086
exec docker run --rm --platform linux/amd64 --cpus "${BENCH_CPUS:-4}" --memory "${BENCH_MEM:-16g}" --user "$(id -u):$(id -g)" $KVM \
    -v "$HERE":/bench:ro -v "$PWD/bench-work":/work $MOUNTS -e HOME=/tmp "$IMAGE" /bench/bench --work /work "$@"
