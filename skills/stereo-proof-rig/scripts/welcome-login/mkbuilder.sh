#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# mkbuilder.sh TAG REPO_DIR [APT_CONF_DIR [SOURCE_DIR...]]: the lane's package builder (the shared sparky-lc-migration:20261020 is
# not on this daemon): Debian testing pinned by digest, the tools the Lean Code toolkit and a Debian rebuild need, and the edition's
# sparky-stereo-problems (the catalog step of lean.standalone), installed from the edition's signed tree at /repo.
# With APT_CONF_DIR (sparky-stereo, sparky-stereo-only-ours, sparky-stereo-deb-multimedia.sources) the edition's tree,
# deb-multimedia and the edition's pins stay configured as on the image, and each SOURCE_DIR's build dependencies (its
# debian/control) are installed and frozen in the image, for recipes that build with no network (stereo-layer).
# Environment: DOCKER_HOST, BASE_IMAGE, HTTPS_ONLY_APT, LOGS, CONTAINER_IDS.
set -euo pipefail
TAG=${1:?tag}; REPO=$(cd "${2:?repo tree}" && pwd); CONF=${3:-}; shift $(( $# < 3 ? $# : 3 ))
: "${BASE_IMAGE:?}" "${HTTPS_ONLY_APT:?}" "${CONTAINER_IDS:?}"
NAME=kw63-mkbuilder-$$
LOGS=${LOGS:-$PWD/builder-logs}; mkdir -p "$LOGS"
mounts=(); sources=""
if [ -n "$CONF" ]; then mounts+=(--mount "type=bind,src=$(cd "$CONF" && pwd),dst=/aptconf,readonly"); fi
i=0
for src in "$@"; do
	mkdir -p "$LOGS/control-$i"; cp "$src/debian/control" "$LOGS/control-$i/control"
	mounts+=(--mount "type=bind,src=$(cd "$src" && pwd)/debian,dst=/src/$i/debian,readonly"); sources="$sources /src/$i"; i=$((i + 1))
done
docker create --name "$NAME" --ulimit core=1 --platform linux/amd64 --cpus 4 \
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly \
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly" \
	--mount "type=bind,src=$REPO,dst=/repo,readonly" --mount "type=bind,src=$LOGS,dst=/logs" "${mounts[@]}" \
	-e "SOURCES=$sources" "$BASE_IMAGE" sh -c '
set -e; export DEBIAN_FRONTEND=noninteractive
sed -i "s/^Types: deb$/Types: deb deb-src/; s/^Components: main$/Components: main contrib non-free non-free-firmware/" /etc/apt/sources.list.d/debian.sources
sh /run/https-only-apt.sh
apt-get -y update > /logs/update0.txt 2>&1
apt-get -y --no-install-recommends install ca-certificates gpg > /logs/boot.txt 2>&1
install -m 644 /repo/sparky-stereo-repo.asc /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc
printf "Types: deb\nURIs: file:/repo\nSuites: mashtabba\nComponents: main\nSigned-By: /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc\n" > /etc/apt/sources.list.d/sparky-stereo-build.sources
if [ -d /aptconf ]; then
	apt-get -y update > /logs/update1.txt 2>&1
	apt-get -y --no-install-recommends install deb-multimedia-keyring > /logs/dmo-keyring.txt 2>&1
	cp /aptconf/sparky-stereo /aptconf/sparky-stereo-only-ours /etc/apt/preferences.d/
	cp /aptconf/sparky-stereo-deb-multimedia.sources /etc/apt/sources.list.d/
	sh /run/https-only-apt.sh
fi
apt-get -y update > /logs/update2.txt 2>&1
apt-get -y --no-install-recommends install build-essential devscripts fakeroot quilt dpkg-dev python3 python3-pil python3-yaml git gettext nodejs node-acorn bubblewrap debian-archive-keyring xz-utils binutils apt-utils sparky-stereo-problems > /logs/install.txt 2>&1 || { tail -30 /logs/install.txt; exit 1; }
for src in $SOURCES; do
	apt-get -y -o Acquire::Retries=5 --no-install-recommends build-dep "$src" >> /logs/build-dep.txt 2>&1 || { tail -40 /logs/build-dep.txt; exit 1; }
done
rm -f /etc/apt/sources.list.d/sparky-stereo-build.sources /etc/apt/sources.list.d/sparky-stereo-deb-multimedia.sources
dpkg-query -W -f "\${Package} \${Version}\n" > /logs/packages.txt
apt-get clean; rm -rf /var/lib/apt/lists/*
chown -R 1000:1000 /logs' > /dev/null
docker inspect -f '{{.Id}}' "$NAME" >> "$CONTAINER_IDS"
status=0; docker start -a "$NAME" || status=$?
if [ "$status" != 0 ]; then docker rm -f "$NAME" > /dev/null; echo "builder failed ($status): $LOGS" >&2; exit "$status"; fi
docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$NAME" "$TAG" > /dev/null
docker rm -f "$NAME" > /dev/null
echo "built $TAG"
