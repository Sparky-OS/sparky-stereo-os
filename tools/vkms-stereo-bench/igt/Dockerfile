# SPDX-License-Identifier: GPL-2.0-or-later
# IGT GPU Tools build and run image for vkms-stereo-bench (kms_3d only). Containers run as the user.
FROM debian:testing@sha256:cf15c569a84dfda832e421ab27a8049e962ba8e90571612396cd8db799279e4e
ENV DEBIAN_FRONTEND=noninteractive LC_ALL=C
RUN apt-get update -qq && apt-get -y install --no-install-recommends \
      build-essential meson ninja-build pkg-config flex bison python3 ca-certificates \
      libdrm-dev libpciaccess-dev libkmod-dev libdw-dev libpixman-1-dev libcairo2-dev \
      libpci-dev libudev-dev libglib2.0-dev libunwind-dev kmod \
      && rm -rf /var/lib/apt/lists/*
ENV HOME=/tmp
