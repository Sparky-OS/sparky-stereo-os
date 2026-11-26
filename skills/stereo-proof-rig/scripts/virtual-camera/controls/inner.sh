#!/bin/bash
# Root part inside the proof container: build the rig's shim and probes, install the package under test with apt (its dependencies
# are already in the image, so nothing is downloaded), make the /dev entries Qt lists, then hand over to rows.sh as uid 1000.
set -euo pipefail
MODE=$1
shift
: "${RUN:?}"
export DEBIAN_FRONTEND=noninteractive
mkdir -p "$RUN/vcam" "$RUN/probes" "$RUN/home"
# the session bus answers only a user it can name: a passwd entry for uid 1000
getent passwd 1000 >/dev/null || echo "rig:x:1000:1000:rig:$RUN/home:/bin/bash" >>/etc/passwd
getent group 1000 >/dev/null || echo "rig:x:1000:" >>/etc/group
cc -shared -fPIC -O1 -o "$RUN/vcam/vcam-shim.so" /rig/vcam-shim.c -ldl
cp /rig/vcam/*.cfg "$RUN/vcam/"
chown -R 1000:1000 "$RUN"
as_user() { setpriv --reuid=1000 --regid=1000 --clear-groups env HOME="$RUN/home" RUN="$RUN" "$@"; }
as_user sh -c "cmake -S /rig/probes -B '$RUN/probes' -G Ninja >'$RUN/probes/cmake.log' 2>&1 && ninja -C '$RUN/probes' >'$RUN/probes/ninja.log' 2>&1" || { tail -n 20 "$RUN/probes/cmake.log"; tail -n 30 "$RUN/probes/ninja.log"; exit 1; }
install_deb() {
	echo "== apt-get install $1"
	apt-get -y --no-install-recommends install "$1" 2>&1 | grep -E '^(Inst|Remv|Setting up|Unpacking|E:)' || true
	echo "installed: sparky-stereo-camera $(dpkg-query -W -f='${Version}' sparky-stereo-camera)"
	dpkg --verify sparky-stereo-camera && echo "dpkg --verify: clean"
}
for n in 30 31 32 33 34 35; do ln -sf "/nonexistent-camera-$n" "/dev/video$n"; done
case $MODE in
red | upgrade) install_deb /deb012/sparky-stereo-camera_0.1.2+lc1_amd64.deb ;;
green) install_deb "$(ls /deb013/sparky-stereo-camera_0.1.3+lc1_amd64.deb)" ;;
esac
if [ "$MODE" = upgrade ]; then
	as_user bash /rig/rows.sh before-upgrade
	install_deb "$(ls /deb013/sparky-stereo-camera_0.1.3+lc1_amd64.deb)"
	as_user bash /rig/rows.sh after-upgrade
else
	as_user bash /rig/rows.sh "$MODE" "$@"
fi
as_user bash /rig/rows.sh stop
