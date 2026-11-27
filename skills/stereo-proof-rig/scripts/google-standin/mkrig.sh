#!/bin/bash
# mkrig.sh TAG: the Plasma rig image for row 299 (DriveSync in KDE), adapted from the proof rig's
# welcome-login/mkrig.sh: Debian testing by image digest, the published round as a file: source with the edition's pins
# (from the published sparky-stereo-apt), deb-multimedia, a Plasma session, both Secret Service owners the image can
# have (GNOME Keyring as published, KDE Wallet with pam_kwallet), the portals, Dolphin, KAccounts and KIO GDrive.
# The edition's local host names are mapped to nothing: no packet leaves for the local network.
# Env: DOCKER_HOST, BASE_IMAGE (an image ID or digest), REPO (published tree), CONF (pin files), HTTPS_ONLY_APT,
#      LOGS (folder), CONTAINER_IDS (the lane's .container-ids).
set -euo pipefail
TAG=${1:?tag}
: "${BASE_IMAGE:?}" "${REPO:?}" "${CONF:?}" "${HTTPS_ONLY_APT:?}" "${LOGS:?}" "${CONTAINER_IDS:?}"
NAME=${PREFIX:-standin}-mkrig-$$
mkdir -p "$LOGS"
docker create --name "$NAME" --ulimit core=1 --platform linux/amd64 --cpus 4 \
	--add-host repo.sparkyos.org:127.0.0.1 --add-host d2server:127.0.0.1 \
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly \
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly" \
	--mount "type=bind,src=$REPO,dst=/repo,readonly" --mount "type=bind,src=$CONF,dst=/aptconf,readonly" \
	--mount "type=bind,src=$LOGS,dst=/logs" "$BASE_IMAGE" sh -c '
set -e; export DEBIAN_FRONTEND=noninteractive
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
PKGS="kwin-wayland kwin-common plasma-workspace plasma-desktop kactivitymanagerd kded6 sparky-stereo-look libkf6config-bin qdbus-qt6 dbus-bin dbus-daemon dbus-x11 python3-gi gir1.2-glib-2.0 python3-pil python3-cryptography wayland-utils xwayland libgl1-mesa-dri libegl-mesa0 mesa-vulkan-drivers procps psmisc fonts-dejavu-core fonts-noto-core locales kwallet6 libpam-kwallet5 gnome-keyring libsecret-tools xdg-desktop-portal xdg-desktop-portal-kde dolphin breeze-icon-theme openssl libglib2.0-bin kaccounts-providers kaccounts-integration kio-gdrive signon-kwallet-extension libgtk-4-1 libadwaita-1-0 xdg-utils sqlite3 gcc libc6-dev libwayland-dev wayland-protocols libwayland-bin"
apt-get -y -o Acquire::Retries=5 --no-install-recommends install $PKGS > /logs/install.txt 2>&1 || { tail -40 /logs/install.txt; exit 1; }
# a package that installs the edition sources file would point apt at the local network: the file source stays the only one
rm -f /etc/apt/sources.list.d/sparky-stereo.sources
sed -i "s/^# *\(en_US.UTF-8\)/\1/; s/^# *\(pt_BR.UTF-8\)/\1/; s/^# *\(de_DE.UTF-8\)/\1/; s/^# *\(ja_JP.UTF-8\)/\1/" /etc/locale.gen; locale-gen > /logs/locale-gen.txt 2>&1
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
