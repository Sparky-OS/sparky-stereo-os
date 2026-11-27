#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../SKILL.md#traps-that-fooled-us) explains.
# SPDX-License-Identifier: MIT
# mkrig.sh TAG REPO_DIR APT_CONF_DIR [EXTRA_DEB_DIR]: the rig image, from a Debian testing base pinned by digest and a signed tree of
# the edition (dists/mashtabba, pool) mounted at /repo. APT_CONF_DIR holds sparky-stereo-apt's pin files (sparky-stereo,
# sparky-stereo-only-ours) and its deb-multimedia source, taken from that package (it needs Sparky's own repository to install).
# The .deb files of EXTRA_DEB_DIR are installed over the tree with apt: their Inst lines are the upgrade's (extra.txt).
# Environment: DOCKER_HOST, BASE_IMAGE (debian:testing@sha256:...), HTTPS_ONLY_APT (the build tree helper tools/https-only-apt.sh),
# NAME_PREFIX, LOGS (a folder for the logs; default ./rig-build-TAG).
set -euo pipefail
TAG=${1:?tag}; REPO=$(cd "${2:?repo tree}" && pwd); CONF=$(cd "${3:?apt configuration}" && pwd); EXTRA=${4:-}
: "${BASE_IMAGE:?debian:testing@sha256:... (pin it by digest)}" "${HTTPS_ONLY_APT:?the build tree helper tools/https-only-apt.sh}"
NAME=${NAME_PREFIX:-splash-rig}-mk-$$
SAFE_TAG=${TAG//:/-}; SAFE_TAG=${SAFE_TAG//\//-}
LOGS=${LOGS:-$PWD/rig-build-$SAFE_TAG}; mkdir -p "$LOGS"
extra=(); [ -n "$EXTRA" ] && extra=(--mount "type=bind,src=$(cd "$EXTRA" && pwd),dst=/extra,readonly")
docker run --name "$NAME" --ulimit core=1 --platform linux/amd64 --cpus 4 \
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly \
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly" \
	--mount "type=bind,src=$REPO,dst=/repo,readonly" --mount "type=bind,src=$CONF,dst=/aptconf,readonly" "${extra[@]}" \
	--mount "type=bind,src=$LOGS,dst=/logs" -e "EXTRA_PACKAGES=${EXTRA_PACKAGES:-}" "$BASE_IMAGE" sh -c '
set -e; ulimit -c 0; export DEBIAN_FRONTEND=noninteractive
sh /run/https-only-apt.sh
apt-get -y update > /logs/update0.txt 2>&1
apt-get -y --no-install-recommends install ca-certificates gpg xz-utils > /logs/boot.txt 2>&1
install -m 644 /repo/sparky-stereo-repo.asc /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc
printf "Types: deb\nURIs: file:/repo\nSuites: mashtabba\nComponents: main\nSigned-By: /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc\n" > /etc/apt/sources.list.d/sparky-stereo.sources
apt-get -y update > /logs/update1.txt 2>&1
apt-get -y -o Acquire::Retries=5 dist-upgrade > /logs/dist-upgrade0.txt 2>&1
apt-get -y --no-install-recommends install deb-multimedia-keyring > /logs/dmo-keyring.txt 2>&1
cp /aptconf/sparky-stereo /aptconf/sparky-stereo-only-ours /etc/apt/preferences.d/
cp /aptconf/sparky-stereo-deb-multimedia.sources /etc/apt/sources.list.d/
sh /run/https-only-apt.sh
apt-get -y update > /logs/update2.txt 2>&1
PKGS="kwin-wayland plasma-workspace plasma-desktop kactivitymanagerd sparky-stereo-look plasma-theme-oxygen libkf6config-bin libkscreen-bin qdbus-qt6 dbus-bin dbus-daemon dbus-x11 python3-gi gir1.2-glib-2.0 python3-numpy python3-pil wayland-utils xwayland libstereo-declare1 qml6-module-qtquick fonts-dejavu-core locales ${EXTRA_PACKAGES:-}"
apt-get -y -o Acquire::Retries=5 dist-upgrade > /logs/dist-upgrade.txt 2>&1
apt-get -y -o Acquire::Retries=5 --no-install-recommends install $PKGS > /logs/install.txt 2>&1 || { tail -30 /logs/install.txt; exit 1; }
# a base image made by this script keeps an empty /extra mount point: install only when debs are there
if ls /extra/*.deb > /dev/null 2>&1; then apt-get -s --no-install-recommends install /extra/*.deb > /logs/extra-simulate.txt 2>&1; apt-get -y --no-install-recommends install /extra/*.deb > /logs/extra.txt 2>&1 || { tail -30 /logs/extra.txt; exit 1; }; fi
useradd -m -u 1000 -s /bin/bash person 2>/dev/null || true
dpkg-query -W -f "\${Package} \${Version}\n" > /logs/packages.txt
apt-get clean; rm -rf /var/lib/apt/lists/*
chown -R 1000:1000 /logs'
docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$NAME" "$TAG" > /dev/null
docker rm -f "$NAME" > /dev/null
