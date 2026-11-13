# SPDX-License-Identifier: GPL-2.0-or-later
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root XDG_RUNTIME_DIR=/run/user/0 LANG=C.UTF-8 LC_ALL=C.UTF-8
export KWIN_DRM_DEVICES=/dev/dri/card0 QT_LOGGING_RULES="kwin_core.debug=true;kwin_wayland_drm.debug=false"
mkdir -p $XDG_RUNTIME_DIR && chmod 700 $XDG_RUNTIME_DIR
ulimit -c 0
dbus-run-session -- sh /tmp/steps.sh
