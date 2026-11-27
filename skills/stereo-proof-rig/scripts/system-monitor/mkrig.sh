#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# mkrig.sh TAG REPO_DIR APT_CONF_DIR [EXTRA_DEB_DIR]: the rig image for System Monitor's Overview presets (queue row 182).
# Adapted from skills/stereo-proof-rig/scripts/welcome-login/mkrig.sh: Debian testing pinned by digest, the edition's
# signed tree mounted at /repo, deb-multimedia, the edition's pins from the published sparky-stereo-apt.
# APT_CONF_DIR: sparky-stereo, sparky-stereo-only-ours, sparky-stereo-deb-multimedia.sources.
# The ten languages' locales and Noto Sans CJK are in the image: the sidebar's titles are measured on screen in each.
# Environment: DOCKER_HOST, BASE_IMAGE (by digest or a lane tag of one), HTTPS_ONLY_APT, LOGS, CONTAINER_IDS.
set -euo pipefail
TAG=${1:?tag}; REPO=$(cd "${2:?repo tree}" && pwd); CONF=$(cd "${3:?apt configuration}" && pwd); EXTRA=${4:-}
: "${BASE_IMAGE:?base image}" "${HTTPS_ONLY_APT:?https-only-apt.sh}" "${CONTAINER_IDS:?.container-ids file}"
NAME=${PREFIX:-sm182}-mkrig-$$
SAFE_TAG=${TAG//:/-}; SAFE_TAG=${SAFE_TAG//\//-}
LOGS=${LOGS:-$PWD/rig-build-$SAFE_TAG}; mkdir -p "$LOGS"
extra=(); [ -n "$EXTRA" ] && extra=(--mount "type=bind,src=$(cd "$EXTRA" && pwd),dst=/extra,readonly")
docker create --name "$NAME" --ulimit core=1 --platform linux/amd64 --cpus 4 \
	--add-host repo.sparkyos.org:127.0.0.1 --add-host d2server:127.0.0.1 \
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly \
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly" \
	--mount "type=bind,src=$REPO,dst=/repo,readonly" --mount "type=bind,src=$CONF,dst=/aptconf,readonly" "${extra[@]}" \
	--mount "type=bind,src=$LOGS,dst=/logs" -e "EXTRA_PACKAGES=${EXTRA_PACKAGES:-}" "$BASE_IMAGE" sh -c '
set -e; export DEBIAN_FRONTEND=noninteractive
sed -i "s/^Components: main$/Components: main contrib non-free non-free-firmware/" /etc/apt/sources.list.d/debian.sources
sh /run/https-only-apt.sh
apt-get -y update > /logs/update0.txt 2>&1
apt-get -y --no-install-recommends install ca-certificates gpg xz-utils > /logs/boot.txt 2>&1
install -m 644 /repo/sparky-stereo-repo.asc /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc
printf "Types: deb\nURIs: file:/repo\nSuites: mashtabba\nComponents: main\nSigned-By: /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc\n" > /etc/apt/sources.list.d/sparky-stereo-local.sources
apt-get -y update > /logs/update1.txt 2>&1
apt-get -y --no-install-recommends install deb-multimedia-keyring > /logs/dmo-keyring.txt 2>&1
cp /aptconf/sparky-stereo /aptconf/sparky-stereo-only-ours /etc/apt/preferences.d/
cp /aptconf/sparky-stereo-deb-multimedia.sources /etc/apt/sources.list.d/
sh /run/https-only-apt.sh
apt-get -y update > /logs/update2.txt 2>&1
apt-get -y -o Acquire::Retries=5 dist-upgrade > /logs/dist-upgrade.txt 2>&1
PKGS="kwin-wayland kwin-common qt6-wayland breeze-icon-theme qml6-module-org-kde-desktop qml6-module-org-kde-kquickcontrols udev gcc libc6-dev libwayland-dev libwayland-bin plasma-systemmonitor ksystemstats libksysguard-bin plasma-integration breeze kded6 libkf6config-bin qdbus-qt6 dbus-bin dbus-daemon dbus-x11 dbus-user-session at-spi2-core python3-pyatspi gir1.2-atspi-2.0 python3-gi python3-pil python3-numpy umockdev lm-sensors pciutils wayland-utils xwayland fonts-noto-core fonts-noto-cjk fonts-dejavu-core locales libgl1-mesa-dri libegl-mesa0 mesa-vulkan-drivers procps psmisc sparky-stereo-problems ${EXTRA_PACKAGES:-}"
apt-get -y -o Acquire::Retries=5 --no-install-recommends install $PKGS > /logs/install.txt 2>&1 || { tail -40 /logs/install.txt; exit 1; }
if [ -d /extra ]; then apt-get -s --no-install-recommends install /extra/*.deb > /logs/extra-simulate.txt 2>&1; apt-get -y --no-install-recommends install /extra/*.deb > /logs/extra.txt 2>&1 || { tail -30 /logs/extra.txt; exit 1; }; fi
for l in en_US pl_PL pt_BR fr_FR de_DE es_ES ja_JP ko_KR zh_CN zh_TW; do sed -i "s/^# *\($l.UTF-8\)/\1/" /etc/locale.gen; done; locale-gen > /logs/locale-gen.txt 2>&1
useradd -m -u 1000 -s /bin/bash person 2>/dev/null || true
rm -f /etc/apt/sources.list.d/sparky-stereo.sources
dpkg-query -W -f "\${Package} \${Version}\n" > /logs/packages.txt
apt-get clean; rm -rf /var/lib/apt/lists/*
chown -R 1000:1000 /logs' > /dev/null
docker inspect -f '{{.Id}}' "$NAME" >> "$CONTAINER_IDS"
status=0; docker start -a "$NAME" || status=$?
if [ "$status" != 0 ]; then docker rm -f "$NAME" > /dev/null; echo "rig build failed ($status): $LOGS" >&2; exit "$status"; fi
docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$NAME" "$TAG" > /dev/null
docker rm -f "$NAME" > /dev/null
echo "built $TAG"
