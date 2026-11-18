#!/bin/bash
# upgrade-test.sh NEWDIR PLYDIR [PERSON]: apt installs sparkyos-plymouth over the published one in a container of its own
# (ORDER 715). The published tree (REPO_PUB, read only) is one apt source, a flat folder holding the successor and the
# Plymouth +stereo3d4 .debs (NEWDIR, PLYDIR) the other, both file: sources. The published set is installed first
# (the first install makes sparkyos-stereo the default, as on a machine that took the image); PERSON names the theme the
# person chose before the upgrade (the package state file is removed and the theme set by hand, as a person who chose it leaves the
# system; default: none, the automatic default stays, which sparky-stereo-plymouth moves to its own on a trigger, ORDER 639).
# CONTROL=1 reinstalls the published package instead of upgrading, to show what that rule does without the successor. Debian testing (https) supplies fonts-cantarell,
# which plymouth-themes needs and the edition's tree does not carry. The proof is apt's own: the Inst lines, the
# Remv count, the configured theme before and after, the maintainer scripts' state file.
# Environment: DOCKER_HOST, REPO_PUB, HTTPS_ONLY_APT, SPARKY_BUILD_IMAGE (an image with dpkg-dev, for dpkg-scanpackages), PREFIX.
set -euo pipefail
NEW=$(realpath "${1:?folder holding the successor sparkyos-plymouth .deb}") PLY=$(realpath "${2:?folder holding the Plymouth +stereo3d4 .debs}")
PERSON=${3:-}
IMAGE=${SPARKY_BUILD_IMAGE:-${PREFIX:-rig}-build:1}
NAME=${PREFIX:-rig}-upgrade${PERSON:+-$PERSON}${CONTROL:+-control}
docker rm "$NAME" >/dev/null 2>&1 || true
docker run --rm --pull=never --name "$NAME" --ulimit core=0 --platform linux/amd64 --user 0 \
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly --mount type=bind,src=${HTTPS_ONLY_APT:?the https-only apt helper script of your lane rules},dst=/run/https-only-apt.sh,readonly \
	--mount type=bind,src=${REPO_PUB:?the published tree (an apt repository folder)},dst=/repo-pub,readonly --mount "type=bind,src=$NEW,dst=/new,readonly" --mount "type=bind,src=$PLY,dst=/ply,readonly" \
	-e PERSON="$PERSON" -e CONTROL="${CONTROL:-}" "$IMAGE" bash -c '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
sh /run/https-only-apt.sh
# Debian testing stays a source (https only) for what the edition does not carry (plymouth-themes needs fonts-cantarell);
# the edition Plymouth wins over Debian by pin, as the edition own pins make it win
printf "Package: plymouth* libplymouth*\nPin: origin deb.debian.org\nPin-Priority: -1\n" > /etc/apt/preferences.d/${PREFIX:-rig}-debian-plymouth
mkdir -p /repo-new && cp /new/*.deb /ply/*.deb /repo-new/ && (cd /repo-new && dpkg-scanpackages . /dev/null > Packages 2>/dev/null)
cat > /etc/apt/sources.list.d/pub.sources <<EOS
Types: deb
URIs: file:///repo-pub
Suites: mashtabba
Components: main
Trusted: yes
EOS
apt-get update -qq
echo "== published set installed"
apt-get -y -qq install plymouth sparkyos-plymouth sparky-stereo-plymouth >/tmp/pub-install.log 2>&1 || { tail -20 /tmp/pub-install.log; exit 1; }
dpkg -l plymouth sparkyos-plymouth sparky-stereo-plymouth | grep ^ii | awk "{print \$2, \$3}"
if [ -n "$PERSON" ]; then rm -f /var/lib/sparkyos-plymouth/theme; plymouth-set-default-theme "$PERSON"; fi
echo "theme before: $(plymouth-set-default-theme) (plymouthd.conf: $(sed -n "s/^Theme=//p" /etc/plymouth/plymouthd.conf))"
echo "state file before: $(cat /var/lib/sparkyos-plymouth/theme 2>/dev/null || echo none)"
md5sum /etc/plymouth/plymouthd.conf > /tmp/conf.before
cat > /etc/apt/sources.list.d/new.sources <<EOS
Types: deb
URIs: file:///repo-new
Suites: ./
Trusted: yes
EOS
apt-get update -qq
if [ -n "$CONTROL" ]; then
echo "== control: the published package again"
apt-get -y --reinstall install sparkyos-plymouth=9~20261102+lc1 2>&1 | grep -E "^(Unpacking|Setting up) sparkyos|upgraded, |E: " || true
echo "theme after: $(plymouth-set-default-theme) (plymouthd.conf: $(sed -n "s/^Theme=//p" /etc/plymouth/plymouthd.conf))"
echo "state file after: $(cat /var/lib/sparkyos-plymouth/theme 2>/dev/null || echo none)"
exit 0
fi
echo "== the upgrade, as apt plans it"
apt-get -s install sparkyos-plymouth | grep -E "^(Inst|Remv)|upgraded, "
echo "== the upgrade"
apt-get -y install sparkyos-plymouth 2>&1 | grep -E "^(Inst|Remv|Setting up sparkyos|Unpacking sparkyos)|upgraded, |E: " || true
dpkg -l plymouth sparkyos-plymouth | grep ^ii | awk "{print \$2, \$3}"
echo "theme after: $(plymouth-set-default-theme) (plymouthd.conf: $(sed -n "s/^Theme=//p" /etc/plymouth/plymouthd.conf))"
echo "state file after: $(cat /var/lib/sparkyos-plymouth/theme 2>/dev/null || echo none)"
md5sum -c /tmp/conf.before || echo "plymouthd.conf changed by the upgrade"
echo "== both themes are there and selectable"
plymouth-set-default-theme --list | tr "\n" " "; echo
dpkg --verify sparkyos-plymouth && echo "dpkg --verify sparkyos-plymouth: clean"
grep -c "Stereo=full-side-by-side" /usr/share/plymouth/themes/sparkyos-stereo/sparkyos-stereo.plymouth | sed "s/^/Stereo= lines in sparkyos-stereo.plymouth: /"
grep -c "Stereo=" /usr/share/plymouth/themes/sparkyos/sparkyos.plymouth | sed "s/^/Stereo= lines in sparkyos.plymouth: /" || true
'
