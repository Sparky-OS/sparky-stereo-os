# SPDX-License-Identifier: GPL-2.0-or-later
# Tool image for vkms-stereo-bench: QEMU, a static BusyBox for the guest, edid-decode, a compiler for the
# static guest programs and for test kernels, and Python with Pillow for the frame analysis.
FROM debian:testing
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        qemu-system-x86 busybox-static edid-decode \
        build-essential bc bison flex libssl-dev libelf-dev cpio kmod git ca-certificates \
        python3 python3-pil linux-libc-dev \
    && rm -rf /var/lib/apt/lists/*
ENV HOME=/tmp
WORKDIR /bench
