#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# mkrig.sh TAG REPO_DIR APT_CONF_DIR [EXTRA_DEB_DIR]: the rig image for the first-login proof of ORDER 63/720.
# Adapted from skills/stereo-proof-rig/scripts/login-splash/mkrig.sh: Debian testing pinned by digest, the edition's signed
# tree mounted at /repo, deb-multimedia and SparkyLinux's own repository (core, tiamat: sparky-welcome and the tools it
# needs), the edition's pins from the published sparky-stereo-apt. The .deb files of EXTRA_DEB_DIR are installed over the
# tree with apt; their Inst lines go to the logs (extra.txt).
# APT_CONF_DIR: sparky-stereo, sparky-stereo-only-ours, sparky-stereo-deb-multimedia.sources, sparkylinux.gpg.
# Environment: DOCKER_HOST, BASE_IMAGE (debian:testing@sha256:...), HTTPS_ONLY_APT, LOGS, CONTAINER_IDS (file to append the ID to).
set -euo pipefail
TAG=${1:?tag}; REPO=$(cd "${2:?repo tree}" && pwd); CONF=$(cd "${3:?apt configuration}" && pwd); EXTRA=${4:-}
: "${BASE_IMAGE:?debian:testing@sha256:... (pin it by digest)}" "${HTTPS_ONLY_APT:?the build tree helper tools/https-only-apt.sh}"
: "${CONTAINER_IDS:?the lane folder .container-ids file}"
NAME=kw63-mkrig-$$
SAFE_TAG=${TAG//:/-}; SAFE_TAG=${SAFE_TAG//\//-}
LOGS=${LOGS:-$PWD/rig-build-$SAFE_TAG}; mkdir -p "$LOGS"
extra=(); [ -n "$EXTRA" ] && extra=(--mount "type=bind,src=$(cd "$EXTRA" && pwd),dst=/extra,readonly")
docker create --name "$NAME" --ulimit core=1 --platform linux/amd64 --cpus 4 \
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
install -m 644 /aptconf/sparkylinux.gpg /etc/apt/trusted.gpg.d/sparkylinux.gpg
printf "Types: deb\nURIs: file:/repo\nSuites: mashtabba\nComponents: main\nSigned-By: /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc\n" > /etc/apt/sources.list.d/sparky-stereo.sources
printf "Types: deb\nURIs: https://repo.sparkylinux.org/\nSuites: core tiamat\nComponents: main\nSigned-By: /etc/apt/trusted.gpg.d/sparkylinux.gpg\n" > /etc/apt/sources.list.d/sparky.sources
apt-get -y update > /logs/update1.txt 2>&1
apt-get -y --no-install-recommends install deb-multimedia-keyring > /logs/dmo-keyring.txt 2>&1
cp /aptconf/sparky-stereo /aptconf/sparky-stereo-only-ours /etc/apt/preferences.d/
cp /aptconf/sparky-stereo-deb-multimedia.sources /etc/apt/sources.list.d/
sh /run/https-only-apt.sh
apt-get -y update > /logs/update2.txt 2>&1
apt-get -y -o Acquire::Retries=5 dist-upgrade > /logs/dist-upgrade.txt 2>&1
PKGS="kwin-wayland kwin-common plasma-workspace plasma-desktop kactivitymanagerd kded6 sparky-stereo-look plasma-theme-oxygen libkf6config-bin libkscreen-bin kscreen systemsettings libkf6kcmutils-bin qdbus-qt6 dbus-bin dbus-daemon dbus-x11 python3-gi gir1.2-glib-2.0 python3-numpy python3-pil wayland-utils xwayland libstereo-declare1 libstereo-layer1 qml6-module-qtquick fonts-dejavu-core fonts-noto-core locales plasma-welcome sparky-stereo-info sparky-stereo-service-defaults sparky-welcome sparky-stereo-hardware libgl1-mesa-dri libegl-mesa0 mesa-vulkan-drivers procps psmisc ${EXTRA_PACKAGES:-}"
apt-get -y -o Acquire::Retries=5 --no-install-recommends install $PKGS > /logs/install.txt 2>&1 || { tail -40 /logs/install.txt; exit 1; }
if [ -d /extra ]; then apt-get -s --no-install-recommends install /extra/*.deb > /logs/extra-simulate.txt 2>&1; apt-get -y --no-install-recommends install /extra/*.deb > /logs/extra.txt 2>&1 || { tail -30 /logs/extra.txt; exit 1; }; fi
sed -i "s/^# *\(en_US.UTF-8\)/\1/; s/^# *\(pt_BR.UTF-8\)/\1/; s/^# *\(de_DE.UTF-8\)/\1/" /etc/locale.gen; locale-gen > /logs/locale-gen.txt 2>&1
useradd -m -u 1000 -s /bin/bash person 2>/dev/null || true
dpkg-query -W -f "\${Package} \${Version}\n" > /logs/packages.txt
apt-get clean; rm -rf /var/lib/apt/lists/*
chown -R 1000:1000 /logs' > /dev/null
docker inspect -f '{{.Id}}' "$NAME" >> "$CONTAINER_IDS"
status=0; docker start -a "$NAME" || status=$?
if [ "$status" != 0 ]; then docker rm -f "$NAME" > /dev/null; echo "rig build failed ($status): $LOGS" >&2; exit "$status"; fi
docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$NAME" "$TAG" > /dev/null
docker rm -f "$NAME" > /dev/null
echo "built $TAG"
