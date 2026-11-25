#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# mklayer.sh BASE_TAG TAG LOGS [PACKAGE ...]: one layer on a rig image, installed by apt with the edition's signed tree
# at /repo and the image's own sources (Debian, deb-multimedia, SparkyLinux), so a dependency that is not on the base
# comes from where the image would get it. PACKAGE is a package name or /extra/NAME.deb (the .deb files of EXTRA_DIR,
# mounted at /extra). apt's plan (Inst, Remv, Conf lines) is kept in LOGS/plan.txt before it runs; the result in
# LOGS/installed.txt; the image committed as TAG (an earlier image of the same tag, this script's own, is removed).
# Environment: DOCKER_HOST, CONTAINER_IDS, HTTPS_ONLY_APT, REPO (the edition's tree), EXTRA_DIR (optional),
#              POST (optional: a shell line run as root after the install, its output in LOGS/post.txt).
set -euo pipefail
BASE=${1:?base tag}; TAG=${2:?tag}; LOGS=$(mkdir -p "${3:?logs}" && cd "$3" && pwd); shift 3
: "${CONTAINER_IDS:?}" "${HTTPS_ONLY_APT:?}" "${REPO:?}"
mounts=(--mount "type=bind,src=$REPO,dst=/repo,readonly" --mount "type=bind,src=$LOGS,dst=/logs"
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly")
[ -n "${EXTRA_DIR:-}" ] && mounts+=(--mount "type=bind,src=$(cd "$EXTRA_DIR" && pwd),dst=/extra,readonly")
name=kw63-mklayer-$$
docker create --name "$name" --ulimit core=1 --cpus 4 --user 0 "${mounts[@]}" -e "PKGS=$*" -e "POST=${POST:-}" "$BASE" sh -c '
set -e; export DEBIAN_FRONTEND=noninteractive
sh /run/https-only-apt.sh > /dev/null
apt-get -y -o Acquire::Retries=5 update > /logs/update.txt 2>&1
apt-get -s --no-install-recommends install $PKGS > /logs/plan.txt 2>&1 || { tail -30 /logs/plan.txt; exit 1; }
apt-get -y -o Acquire::Retries=5 --no-install-recommends install $PKGS > /logs/install.txt 2>&1 || { tail -30 /logs/install.txt; exit 1; }
[ -z "$POST" ] || sh -c "$POST" > /logs/post.txt 2>&1
dpkg --audit > /logs/audit.txt 2>&1
dpkg-query -W -f "\${Package} \${Version}\n" > /logs/installed.txt
apt-get clean; rm -rf /var/lib/apt/lists/*
chown -R 1000:1000 /logs' > /dev/null
docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
status=0; docker start -a "$name" || status=$?
if [ "$status" = 0 ]; then
	old=$(docker image inspect -f '{{.Id}}' "$TAG" 2>/dev/null || true)
	docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$name" "$TAG" > /dev/null
	new=$(docker image inspect -f '{{.Id}}' "$TAG")
	[ -n "$old" ] && [ "$old" != "$new" ] && docker rmi "$old" > /dev/null
fi
docker rm -f "$name" > /dev/null
[ "$status" = 0 ] && echo "built $TAG" || { echo "layer failed ($status)" >&2; exit "$status"; }
