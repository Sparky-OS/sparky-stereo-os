# SPDX-License-Identifier: GPL-2.0-or-later
# IGT GPU Tools build and run image for vkms-stereo-bench (kms_3d only). Containers run as the user.
FROM debian:testing
ENV DEBIAN_FRONTEND=noninteractive LC_ALL=C
RUN apt-get update -qq && apt-get -y install --no-install-recommends \
      build-essential meson ninja-build pkg-config flex bison python3 ca-certificates \
      libdrm-dev libpciaccess-dev libkmod-dev libdw-dev libpixman-1-dev libcairo2-dev \
      libpci-dev libudev-dev libglib2.0-dev libunwind-dev kmod \
      && rm -rf /var/lib/apt/lists/*
ENV HOME=/tmp
