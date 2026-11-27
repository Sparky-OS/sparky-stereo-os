#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# apt-plan.sh STAGE_DEBS OUT: apt's plan for installing the staged drivesync on a bare Debian testing with the published
# round r1123a and the edition's pins, read from apt's Inst and Remv lines (the rig's Plasma set is the rig layer's own
# install, made by the layer that installs the package).
# Env: DOCKER_HOST, REPO, CONF, HTTPS_ONLY_APT, BASE_IMAGE, CONTAINER_IDS.
set -euo pipefail
DEBS=$(cd "${1:?}" && pwd); OUT=$(mkdir -p "${2:?}" && cd "$2" && pwd)
: "${REPO:?}" "${CONF:?}" "${HTTPS_ONLY_APT:?}" "${BASE_IMAGE:?}" "${CONTAINER_IDS:?}"
common=(--ulimit core=1 --platform linux/amd64 --cpus 2 --add-host repo.sparkyos.org:127.0.0.1 --add-host d2server:127.0.0.1
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly"
	--mount "type=bind,src=$REPO,dst=/repo,readonly" --mount "type=bind,src=$CONF,dst=/aptconf,readonly"
	--mount "type=bind,src=$DEBS,dst=/debs,readonly" --mount "type=bind,src=$OUT,dst=/out")
local_repo='mkdir -p /local && cp /debs/*.deb /local/ && (cd /local && dpkg-scanpackages . > Packages 2>/dev/null)
echo "deb [trusted=yes] file:/local ./" > /etc/apt/sources.list.d/local.list'
run() {
	local name=$1 image=$2 script=$3
	docker create --name "$name" "${common[@]}" "$image" bash -c "$script" > /dev/null
	docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
	local status=0; docker start -a "$name" || status=$?
	docker rm -f "$name" > /dev/null
	return "$status"
}
run "${PREFIX:-standin}-aptplan" "$BASE_IMAGE" "set -e; export DEBIAN_FRONTEND=noninteractive; sh /run/https-only-apt.sh >/dev/null
apt-get -y update >/dev/null 2>&1; apt-get -y --no-install-recommends install ca-certificates dpkg-dev >/dev/null 2>&1
install -m 644 /repo/sparky-stereo-repo.asc /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc
printf 'Types: deb\nURIs: file:/repo\nSuites: mashtabba\nComponents: main\nSigned-By: /etc/apt/trusted.gpg.d/sparky-stereo-repo.asc\n' > /etc/apt/sources.list.d/sparky-stereo-local.sources
apt-get -y update >/dev/null 2>&1; apt-get -y --no-install-recommends install deb-multimedia-keyring >/dev/null 2>&1
cp /aptconf/sparky-stereo /aptconf/sparky-stereo-only-ours /etc/apt/preferences.d/; cp /aptconf/sparky-stereo-deb-multimedia.sources /etc/apt/sources.list.d/
sh /run/https-only-apt.sh >/dev/null
$local_repo
apt-get -y update > /out/b-update.txt 2>&1
apt-get -s install drivesync > /out/b-plan.txt 2>&1
echo \"b: Inst \$(grep -c '^Inst' /out/b-plan.txt) Remv \$(grep -c '^Remv' /out/b-plan.txt)\"
chown -R $(id -u):$(id -g) /out"
