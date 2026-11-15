#!/bin/bash
# Runs as root inside the throwaway container: installs the Qt Multimedia under test, makes the device nodes the
# virtual cameras stand for, and hands over to scenario.sh as the lane's user. Usage: in-container.sh NAME DEB_DIR
set -euo pipefail
NAME=$1 DEBS=$2
RIG=${RIG:?the scripts/virtual-camera folder}
W=${WORK:?a scratch folder}
ulimit -c 0
cd "$DEBS"
dpkg -i $(ls libstereo-*.deb 2>/dev/null) libqt6multimedia6_*_amd64.deb libqt6multimediawidgets6_*_amd64.deb libqt6spatialaudio6_*_amd64.deb \
	qml6-module-qtmultimedia_*_amd64.deb qml6-module-qtquick3d-spatialaudio_*_amd64.deb qt6-multimedia-dev_*_amd64.deb \
	>"$W/evidence/$NAME-dpkg.log" 2>&1
dpkg-query -W -f='INSTALLED ${Package} ${Version}\n' libqt6multimedia6 qml6-module-qtmultimedia | tee -a "$W/evidence/$NAME-dpkg.log"
# a broken symbolic link is what QDir::System lists in /dev besides device nodes; the preload answers open() for it,
# and the user may plug and unplug "cameras" by making and removing links (the container's /dev is its own)
chmod 0777 /dev
for n in 20 21 23; do ln -s /nonexistent-camera /dev/video$n; done
rm -rf "$W/home-$NAME" "$W/vcam-$NAME"
mkdir -p "$W/home-$NAME" "$W/vcam-$NAME"
cp "$RIG"/vcam/*.cfg "$W/vcam-$NAME/"
chown -R 1000:1000 "$W/home-$NAME" "$W/vcam-$NAME"
exec setpriv --reuid=1000 --regid=1000 --clear-groups env \
	HOME="$W/home-$NAME" XDG_RUNTIME_DIR="$W/home-$NAME/run" XDG_STATE_HOME="$W/home-$NAME/state" XDG_CONFIG_HOME="$W/home-$NAME/config" \
	VCAM_ROOT="$W/vcam-$NAME" QT_QPA_PLATFORM=offscreen NAME="$NAME" bash "$RIG/scenario.sh"
