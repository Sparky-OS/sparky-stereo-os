#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# unit-case.sh IMAGE OUT skipped|started: Sparky Welcome's first-run unit under a real user manager, in a throwaway
# container of IMAGE with systemd as PID 1 (sparky-stereo-welcome's tests/first-run-unit.sh, the way
# sparky-backup-core-stereo's tests/setxkb-live-only.sh runs); dbus-user-session, which the image lacks, is installed in
# the container first (from Debian, with the edition's tree at /repo). The test's output and exit status in OUT.
# Environment: DOCKER_HOST, CONTAINER_IDS, HTTPS_ONLY_APT, REPO, TESTS (the recipe's tests folder).
set -uo pipefail
IMG=$1; OUT=$(mkdir -p "$2" && cd "$2" && pwd); WANT=$3
: "${CONTAINER_IDS:?}" "${HTTPS_ONLY_APT:?}" "${REPO:?}" "${TESTS:?}"
name=kw63-unit-$$
docker run -d --name "$name" --ulimit core=1 --cpus 2 --cgroupns=private --security-opt writable-cgroups=true \
	--tmpfs /run --tmpfs /tmp --mount "type=bind,src=$REPO,dst=/repo,readonly" --mount "type=bind,src=$TESTS,dst=/tests,readonly" \
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly \
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly" "$IMG" /lib/systemd/systemd > /dev/null
docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
for i in $(seq 30); do docker exec "$name" systemctl is-system-running 2>/dev/null | grep -q -E 'running|degraded' && break; sleep 1; done
docker exec "$name" sh -c 'sh /run/https-only-apt.sh >/dev/null && apt-get -qq update >/dev/null 2>&1 && DEBIAN_FRONTEND=noninteractive apt-get -qq -y --no-install-recommends install dbus-user-session >/dev/null 2>&1 && echo "dbus-user-session installed"' > "$OUT/setup.txt" 2>&1
docker exec "$name" bash /tests/first-run-unit.sh "$WANT" > "$OUT/test.txt" 2>&1; status=$?
echo "exit $status" >> "$OUT/test.txt"
docker rm -f "$name" > /dev/null
exit "$status"
