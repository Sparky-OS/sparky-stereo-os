#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# live-seed.sh IMAGE SEED: the live user's home as live-config leaves it at boot, for the live rows: the image's own
# live-config hook of sparky-stereo-welcome (/usr/lib/live/config/1187-sparky-stereo-welcome) run as root with
# LIVE_USERNAME=person over SEED mounted as /home/person (live-config sources its hooks with LIVE_USERNAME set; a
# container cannot boot the live medium). The hook's output and the file it wrote go to SEED/../live-seed.txt.
# Environment: DOCKER_HOST, CONTAINER_IDS.
set -euo pipefail
IMG=$1; SEED=$(mkdir -p "$2" && cd "$2" && pwd)
name=kw63-liveseed-$$
docker create --name "$name" --ulimit core=1 --network none --cpus 1 --user 0 --mount "type=bind,src=$SEED,dst=/home/person" "$IMG" sh -c '
mkdir -p /var/lib/live/config
LIVE_USERNAME=person sh -x /usr/lib/live/config/1187-sparky-stereo-welcome 2>&1
echo "== /home/person/.config/plasma-welcomerc"; cat /home/person/.config/plasma-welcomerc
ls -ln /home/person/.config/plasma-welcomerc; ls /var/lib/live/config/' > /dev/null
docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
docker start -a "$name" > "$SEED/../live-seed.txt" 2>&1; status=$?
docker rm -f "$name" > /dev/null
exit $status
