#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# mkcandidate.sh BASE_TAG TAG DEB_DIR LOGS: the candidate rig, one layer on the published rig: the .deb files of DEB_DIR
# installed with dpkg (their dependencies are all on the published rig), dpkg --audit kept, the image committed as TAG.
# Environment: DOCKER_HOST, CONTAINER_IDS.
set -euo pipefail
BASE=${1:?base tag}; TAG=${2:?tag}; DEBS=$(cd "${3:?deb folder}" && pwd); LOGS=$(mkdir -p "${4:?logs}" && cd "$4" && pwd)
: "${CONTAINER_IDS:?}"
name=kw63-mkcand-$$
docker create --name "$name" --ulimit core=1 --cpus 4 --user 0 --network none \
	--mount "type=bind,src=$DEBS,dst=/extra,readonly" --mount "type=bind,src=$LOGS,dst=/logs" "$BASE" sh -c '
set -e; export DEBIAN_FRONTEND=noninteractive
dpkg -i /extra/*.deb > /logs/dpkg-install.txt 2>&1 || { tail -20 /logs/dpkg-install.txt; exit 1; }
dpkg --audit > /logs/audit.txt 2>&1
dpkg-query -W -f "\${Package} \${Version}\n" plasma-welcome sparky-stereo-welcome sparky-stereo-info > /logs/installed.txt
ls /usr/share/plasma/plasma-welcome/first-pages/ > /logs/first-pages.txt
ls /etc/xdg/plasma-welcomerc > /logs/welcomerc-after.txt 2>&1 || true
chown -R 1000:1000 /logs' > /dev/null
docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
status=0; docker start -a "$name" || status=$?
if [ "$status" = 0 ]; then
	old=$(docker image inspect -f '{{.Id}}' "$TAG" 2>/dev/null || true)
	docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$name" "$TAG" > /dev/null
	new=$(docker image inspect -f '{{.Id}}' "$TAG")
	# the earlier image of this tag, now untagged, is this script's own
	[ -n "$old" ] && [ "$old" != "$new" ] && docker rmi "$old" > /dev/null
fi
docker rm -f "$name" > /dev/null
[ "$status" = 0 ] && echo "built $TAG" || { echo "candidate failed ($status)" >&2; exit "$status"; }
