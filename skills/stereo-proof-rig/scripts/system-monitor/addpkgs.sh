#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# addpkgs.sh IMAGE PACKAGE...: install more packages into the rig image as one more layer (the edition's tree at /repo,
# Debian testing, the pins already in the image) and tag the result as IMAGE again (the old image stays as its parent).
# Environment: DOCKER_HOST, CONTAINER_IDS, LOGS, REPO (the published tree), HTTPS_ONLY_APT (the build tree's helper).
set -euo pipefail
IMAGE=${1:?image}; shift
: "${DOCKER_HOST:?}" "${CONTAINER_IDS:?}" "${LOGS:?}" "${REPO:?the published tree}" "${HTTPS_ONLY_APT:?https-only-apt.sh}"
NAME=${PREFIX:-sm182}-addpkgs-$$
mkdir -p "$LOGS"
docker create --name "$NAME" --ulimit core=1 --platform linux/amd64 --cpus 4 \
	--add-host repo.sparkyos.org:127.0.0.1 --add-host d2server:127.0.0.1 \
	-v /etc/ssl/certs/ca-certificates.crt:/run/host-ca.crt:ro -v "$HTTPS_ONLY_APT":/run/https-only-apt.sh:ro \
	-v "$REPO":/repo:ro -v "$LOGS":/logs -e "PKGS=$*" "$IMAGE" sh -c '
set -e; export DEBIAN_FRONTEND=noninteractive
sh /run/https-only-apt.sh
apt-get -y update > /logs/add-update.txt 2>&1
apt-get -y --no-install-recommends install $PKGS > /logs/add-install.txt 2>&1 || { tail -30 /logs/add-install.txt; exit 1; }
dpkg-query -W -f "\${Package} \${Version}\n" > /logs/packages.txt
apt-get clean; rm -rf /var/lib/apt/lists/*
chown -R 1000:1000 /logs' > /dev/null
docker inspect -f '{{.Id}}' "$NAME" >> "$CONTAINER_IDS"
docker start -a "$NAME"
docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$NAME" "$IMAGE" > /dev/null
docker rm -f "$NAME" > /dev/null
echo "added to $IMAGE: $*"
