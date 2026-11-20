# SPDX-License-Identifier: MIT
# nv-env.sh: the session environment Sparky Stereo OS sets at login on a desktop drawn by NVIDIA (published
# sparky-stereo-hardware 0.1.32+lc1, unpacked in /w/hw), with the person's choice desktop=nvidia, opengl=zink.
mkdir -p /tmp/sp-etc
printf 'desktop=nvidia\nopengl=zink\n' > /tmp/sp-etc/opengl-stereo.conf
export SPARKY_STEREO_OPENGL_CONF=/tmp/sp-etc/opengl-stereo.conf
export SPARKY_STEREO_HARDWARE_LIB=/w/hw/usr/lib/sparky-stereo-hardware
export SPARKY_STEREO_HARDWARE_SHARE=/w/hw/usr/share/sparky/sparky-stereo-hardware
. /w/hw/etc/xdg/plasma-workspace/env/sparky-stereo-opengl.sh
