#!/bin/bash
# One command for the unit tests and the container proof of a Universal Media Server change.
# Offline: it needs only three local images (below), a Maven repository cache and a scratch folder.
# One line per unit-test class and per proof case ("PASS" or "FAIL" first); exit status 0 only
# when every line passes and the controls went red as they must.
#
#   rerun.sh                run everything
#   rerun.sh --unit         unit tests only
#   rerun.sh --proof        container proof only (builds the jar first)
#   rerun.sh --pc           only the PC as a renderer (Rygel), after the build
#   rerun.sh --keep         leave the containers running afterwards
#
# Container work only: no package program runs on the host.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
SRC=${UMS_SRC:?set UMS_SRC to the UniversalMediaServer checkout (another tree gives a red run against an older commit)}
PROOF=$HERE/proof
SCR=${UMS_PROOF_SCRATCH:?set UMS_PROOF_SCRATCH to a scratch folder with 2 GB free}
RUN=${UMS_PROOF_RUN:-$SCR/rerun}                    # the work area; give a red run its own
# the Docker daemon is the caller's: export DOCKER_HOST before running
IMAGE_JAVA=${UMS_PROOF_IMAGE_JAVA:?an image with a JDK 17, Maven, FFmpeg and libmediainfo0v5}
IMAGE_TOOLS=${UMS_PROOF_IMAGE_TOOLS:?an image with FFmpeg (libx264), ffprobe and Python 3}
IMAGE_RENDERER=${UMS_PROOF_IMAGE_RENDERER:?an image with Python 3}
NETWORK=${UMS_PROOF_NETWORK:?an internal Docker network with the subnet 192.0.2.0/24: docker network create --internal --subnet 192.0.2.0/24 NAME}
SERVER_UUID=2ca2b70d-2311-443e-8018-c240aa56a4c9
UID_GID="$(id -u):$(id -g)"
MVN_FLAGS=(-o -B -Dmaven.gitcommitid.skip=true -Dskip.installnodecorepack -Dskip.corepack -Dmaven.antrun.skip=true -Dmaven.repo.local=/work/m2repo)

do_unit=1; do_proof=1; keep=0; only_pc=0
for argument in "$@"; do
  case $argument in
    --unit) do_proof=0 ;;
    --proof) do_unit=0 ;;
    --keep) keep=1 ;;
    --pc) do_unit=0; only_pc=1 ;;
    *) echo "usage: $0 [--unit|--proof] [--keep]" >&2; exit 2 ;;
  esac
done

failures=0
line() { printf '%s\n' "$*"; case $1 in FAIL*) failures=$((failures + 1)) ;; esac; }
stop() { echo "STOP: $*" >&2; exit 2; }

free_gb=$(df -BG --output=avail "$SCR" | tail -1 | tr -dc 0-9)
[ "${free_gb:-0}" -ge 2 ] || stop "blocked (disk): $SCR has under 2 GB free"
mkdir -p "$SCR" "$RUN"

containers() { docker ps -a --filter name=ums-proof- --format '{{.Names}}'; }
cleanup() {
  [ "$keep" = 1 ] && return
  for name in $(containers); do docker rm -f "$name" > /dev/null 2>&1; done
}
trap cleanup EXIT

# a scratch folder this script owns: refuse any path that is not under $SCR
fresh() {
  case $1 in "$SCR"/?*) ;; *) stop "refusing to clear $1" ;; esac
  [ -d "$1" ] && rm -rf -- "$1"
  mkdir -p "$1"
}

maven() { # name of the container, then the Maven arguments
  local name=$1; shift
  docker run --rm --name "$name" --cpus 4 --ulimit core=0 --network none --user "$UID_GID" \
    -e HOME=/work/home -v "$RUN:/work" -w /work/src --entrypoint mvn "$IMAGE_JAVA" "${MVN_FLAGS[@]}" "$@"
}

sync_source() {
  [ -d "$RUN/m2repo" ] || { [ -d "$SCR/m2/repository" ] && cp -a "$SCR/m2/repository" "$RUN/m2repo"; } \
    || stop "no Maven cache: expected $SCR/m2/repository (a repository filled once with network access)"
  mkdir -p "$RUN/home" "$RUN/src"
  rsync -a --delete --exclude target --exclude 'react-client/node*' --exclude .git "$SRC/" "$RUN/src/"
  if git -C "$SRC" rev-parse --git-dir > /dev/null 2>&1; then
    echo "SOURCE $(git -C "$SRC" rev-parse --short HEAD)$(git -C "$SRC" status --porcelain | grep -q . && echo ' plus uncommitted changes')"
  else
    echo "SOURCE $SRC (not a git checkout)"
  fi
}

# ---- unit tests -----------------------------------------------------------------------------
# FFmpegParserTest#testParser is left out: it expects "Format Profile: flv" from the FFmpeg that
# UMS bundles, and fails the same way on upstream's own commit 214f75423 with this image's FFmpeg 6.1.1.
unit_tests() {
  maven ums-proof-unit -Dtest='StoreItemStereoTest,FramePackingParserTest,RendererConfigurationTest,StereoConversionFilterTest,FramePackingFilterTest,FFmpegParserTest#checkerboardIsAModeWhenParsedByFFmpeg' \
    -Dsurefire.failIfNoSpecifiedTests=false test > "$SCR/rerun-unit.log" 2>&1
  local status=$?
  local reports=$RUN/src/target/surefire-reports
  local count=0
  for report in "$reports"/*.txt; do
    [ -f "$report" ] || continue
    count=$((count + 1))
    local summary; summary=$(grep -m1 'Tests run' "$report")
    case $summary in
      *"Failures: 0, Errors: 0"*) line "PASS unit $(basename "$report" .txt): $(sed -E "s/^Tests run: ([0-9]+),.*/\1/" <<< "$summary") tests, no failures" ;;
      *) line "FAIL unit $(basename "$report" .txt): $summary" ;;
    esac
  done
  [ "$count" -gt 0 ] || line "FAIL unit: no report; see $SCR/rerun-unit.log"
  [ "$status" -eq 0 ] || [ "$failures" -gt 0 ] || line "FAIL unit: Maven exited $status; see $SCR/rerun-unit.log"
}

# ---- the container proof -------------------------------------------------------------------
JAR=
build_jar() {
  # package ends in an assembly step that needs UMS's own FFmpeg download and fails offline;
  # the jar with its dependencies is built before it, so the jar's age is the check
  local before; before=$(date +%s)
  maven ums-proof-package -DskipTests package > "$SCR/rerun-package.log" 2>&1
  JAR=$(ls "$RUN"/src/target/ums-*-jar-with-dependencies.jar 2>/dev/null | head -1)
  if [ -n "$JAR" ] && [ "$(stat -c %Y "$JAR")" -ge "$before" ]; then
    line "PASS package: $(basename "$JAR") $(sha256sum "$JAR" | cut -c1-12)"
  else
    line "FAIL package: no fresh jar; see $SCR/rerun-package.log"
    JAR=
  fi
}

assemble_home() { # jar
  local template=$SCR/cache/ums-home-template
  if [ ! -d "$template" ]; then
    mkdir -p "$template"
    local tarball; tarball=$(ls "$SRC"/target/ums-*-distribution.tar.gz 2>/dev/null | head -1)
    [ -n "$tarball" ] || stop "no $template and no distribution tarball to make it from"
    tar -xzf "$tarball" -C "$template" --strip-components=1 --exclude='*/ums.jar' --exclude='*/renderers'
  fi
  fresh "$RUN/ums-home"
  cp -a "$template/." "$RUN/ums-home/"
  cp "$1" "$RUN/ums-home/ums.jar"
  mkdir -p "$RUN/ums-home/renderers"
  cp "$SRC"/src/main/external-resources/renderers/*.conf "$RUN/ums-home/renderers/"
  cp "$PROOF"/profiles/*.conf "$RUN/ums-home/renderers/"
}

fixtures() {
  local sum; sum=$(sha256sum "$PROOF/generate-fixtures.sh" | cut -c1-16)
  if [ "$(cat "$SCR/fixtures/.generated" 2>/dev/null)" != "$sum" ]; then
    fresh "$SCR/fixtures"
    docker run --rm --name ums-proof-fixtures --cpus 4 --ulimit core=0 --network none --user "$UID_GID" \
      -v "$PROOF:/proof:ro" -v "$SCR/fixtures:/out" --entrypoint sh "$IMAGE_TOOLS" \
      /proof/generate-fixtures.sh /out/media /out/probes > "$SCR/rerun-fixtures.log" 2>&1 \
      || { line "FAIL fixtures: see $SCR/rerun-fixtures.log"; return 1; }
    echo "$sum" > "$SCR/fixtures/.generated"
  fi
  (cd "$SCR/fixtures/media" && sha256sum -- *.mkv) > "$RUN/fixtures.sha256"
  line "PASS fixtures: $(ls "$SCR/fixtures/media" | wc -l) files"
}

start_server() {
  fresh "$RUN/profile"; mkdir -p "$RUN/profile/data" "$RUN/home/.config/UMS"
  cat > "$RUN/profile/UMS.conf" <<EOF
server_name = UMS 94 Proof
append_profile_name = true
port = 5001
scan_shared_folders_on_startup = true
web_gui_port = 9001
log_level = DEBUG
shared_folders = /media
uuid = $SERVER_UUID
EOF
  printf '[\n  {\n    "file": "/media",\n    "monitored": true,\n    "metadata": true,\n    "active": true,\n    "groups": [],\n    "type": "Folder"\n  }\n]\n' > "$RUN/profile/SHARED.conf"
  docker run -d --name ums-proof-server --network "$NETWORK" --ip 192.0.2.1 --cpus 4 --ulimit core=0 --user "$UID_GID" \
    -e JAVA_OPTS=-Duser.home=/home/ums -v "$RUN/home:/home/ums" -v "$RUN/profile:/home/ums/.config/UMS" \
    -v "$RUN/ums-home:/opt/ums" -v "$SCR/fixtures/media:/media:ro" -w /opt/ums --entrypoint ./UMS.sh \
    "$IMAGE_JAVA" -console > /dev/null || return 1
  local waited=0
  until docker logs ums-proof-server 2>&1 | grep -q 'Media scan completed'; do
    sleep 2; waited=$((waited + 2))
    [ "$waited" -lt 150 ] || { line "FAIL server: no 'Media scan completed' in 150 s"; return 1; }
  done
  line "PASS server: scan completed in about $waited s"
}

instances() { python3 -I -c "
import json,sys
for name, i in json.load(open('$PROOF/cases.json'))['instances'].items():
    print(name, i['ip'], i['identity'], i['user_agent'].replace(' ', '_'), 'ssdp' if i['ssdp'] else 'no-ssdp', 'control' if i.get('control_only') else 'cases')"; }

start_renderers() {
  fresh "$RUN/records"
  while read -r name ip identity agent ssdp role; do
    agent=${agent//_/ }
    mkdir -p "$RUN/records/$name"
    local extra=(); [ "$ssdp" = no-ssdp ] && extra=(--no-ssdp)
    docker run -d --name "ums-proof-r-$name" --network "$NETWORK" --ip "$ip" --cpus 1 --ulimit core=0 --user "$UID_GID" \
      -v "$PROOF/emulated-renderer.py:/proof/emulated-renderer.py:ro" -v "$RUN/records/$name:/records" "$IMAGE_RENDERER" \
      python3 /proof/emulated-renderer.py --host "$ip" --port 8000 --record-dir /records --identity "$identity" \
      --user-agent "$agent" "${extra[@]}" > /dev/null || return 1
  done < <(instances)
  sleep 12   # two rounds of SSDP alive from the renderers that announce themselves
}

controller() { # instance, ip, agent, then the proof.py arguments
  local name=$1 ip=$2 agent=$3; shift 3
  docker run --rm --name "ums-proof-c-$name" --network "container:ums-proof-r-$name" --cpus 2 --ulimit core=0 --user "$UID_GID" \
    -v "$PROOF:/proof:ro" -v "$RUN/records/$name:/records" "$IMAGE_TOOLS" python3 /proof/proof.py "$@"
}

proof_cases() {
  while read -r name ip identity agent ssdp role; do
    agent=${agent//_/ }
    [ "$role" = control ] && continue
    local output; output=$(controller "$name" "$ip" "$agent" stream --cases /proof/cases.json --instance "$name" \
      --server-ip 192.0.2.1 --renderer "http://$ip:8000" --user-agent "$agent")
    local status=$?
    if [ "$name" = generic ]; then
      # the control: a renderer without a profile must NOT get the converted picture
      if [ "$status" -ne 0 ] && grep -q '^FAIL' <<< "$output"; then
        line "PASS control: $(grep -m1 '^FAIL' <<< "$output" | cut -c1-220)"
        line "PASS control went red as it must (a renderer without a profile gets no conversion)"
      else
        line "FAIL control: the check passed on an unconverted stream, so it proves nothing"
      fi
      continue
    fi
    while IFS= read -r result; do line "$result"; done <<< "$output"
    [ -n "$output" ] || line "FAIL $name: the controller printed nothing (exit $status)"
  done < <(instances)
}

log_checks() {
  # the debug file of the profile holds the DEBUG lines (the console prints from INFO)
  cp "$RUN/profile/debug.log" "$SCR/rerun-server-debug.log" 2>/dev/null
  local log; log=$(cat "$SCR/rerun-server-debug.log" 2>/dev/null; docker logs ums-proof-server 2>&1)
  local matched; matched=$(grep -m1 'Matched media renderer "Flat Headset" based on dlna details' <<< "$log" | cut -c1-230)
  [ -n "$matched" ] && line "PASS ssdp: the emulated headset, announced on SSDP, matched FlatHeadset.conf: ${matched#*Matched }" \
    || line "FAIL ssdp: the server log never matched the emulated headset to the Flat Headset profile"
  matched=$(grep -m1 'Matched media renderer "Sony Bravia EX725" based on dlna details' <<< "$log" | cut -c1-230)
  [ -n "$matched" ] && line "PASS ssdp: the emulated Bravia matched Sony-BraviaEX725.conf: ${matched#*Matched }" \
    || line "FAIL ssdp: the server log never matched the emulated Bravia to its profile"
  grep -qF 'No supported conversion can convert "anaglyph-cyan-red.mkv" from "Anaglyph (cyan/red)" to "sbsl", so it is not offered to Flat Headset' <<< "$log" \
    && line "PASS warning: an unconvertible file is refused aloud (WARN naming file, layout and renderer)" \
    || line "FAIL warning: no WARN for anaglyph-cyan-red.mkv in the server log"
  (cd "$SCR/fixtures/media" && sha256sum --quiet -c "$RUN/fixtures.sha256") \
    && line "PASS source files: sha256 of every fixture unchanged after the run" \
    || line "FAIL source files: a fixture changed"
}

proof_pc() {
  # the PC as a renderer: Rygel's MPRIS plugin in front of an MPRIS2 player (VLC), a film pushed from UMS
  if ! docker image inspect ums-proof-rygel:1 > /dev/null 2>&1; then
    echo "SKIP pc: image ums-proof-rygel:1 is missing (rygel/build.sh builds it; it needs the network once)"
    return
  fi
  mkdir -p "$RUN/records/pc"
  docker run -d --name ums-proof-r-pc --network "$NETWORK" --ip 192.0.2.10 --cpus 1 --ulimit core=0 --user "$UID_GID" \
    -v "$RUN/records/pc:/records" ums-proof-rygel:1 > /dev/null || { line "FAIL pc: the container did not start"; return; }
  sleep 12
  local output; output=$(docker run --rm --name ums-proof-c-pc --network container:ums-proof-r-pc --cpus 2 --ulimit core=0 --user "$UID_GID" \
    -v "$PROOF:/proof:ro" -v "$RUN/records/pc:/records" "$IMAGE_TOOLS" python3 /proof/pc.py --address 192.0.2.10 \
    --server-ip 192.0.2.1 --user-agent ProofController/1.0 --title seek-sbs)
  while IFS= read -r result; do line "$result"; done <<< "$output"
  [ -n "$output" ] || line "FAIL pc: the controller printed nothing"
  local probe; probe=$(docker exec ums-proof-r-pc pc-probe.sh 2>&1)
  local url; url=$(cat "$RUN/records/pc/pushed-url.txt" 2>/dev/null)
  grep -q '^status=.*Playing' <<< "$probe" && line "PASS pc player: the MPRIS2 player says Playing ($(grep -m1 '^player=' <<< "$probe" | cut -d= -f2))" \
    || line "FAIL pc player: the MPRIS2 player is not Playing: $(grep -m1 '^status=' <<< "$probe")"
  [ -n "$url" ] && grep -qF "$url" <<< "$probe" && line "PASS pc player: its xesam:url is the URL UMS gave" \
    || line "FAIL pc player: its metadata does not carry the URL UMS gave"
  cp "$RUN/profile/debug.log" "$SCR/rerun-server-debug.log" 2>/dev/null
  grep -q '"seek-sbs.mkv" will be streamed' "$SCR/rerun-server-debug.log" \
    && line 'PASS pc stream: UMS sent the file as it is (final verdict "will be streamed", no conversion)' \
    || line 'FAIL pc stream: the server did not stream seek-sbs.mkv as it is'
  grep -qE 'Matched media renderer "PC stereo player \(Rygel MPRIS\)"' "$SCR/rerun-server-debug.log" \
    && line "PASS pc ssdp: Rygel's description matched the PC profile" \
    || line "FAIL pc ssdp: the server never matched Rygel's description to the PC profile"
  cp "$RUN/records/pc/rygel.log" "$SCR/rerun-rygel.log" 2>/dev/null
  cp "$RUN/records/pc/player.log" "$SCR/rerun-player.log" 2>/dev/null
}

proof_controls() {
  local ip=192.0.2.9 agent="ProofControl/1.0"
  local url="http://192.0.2.1:5001/ums/media/none"
  local output; output=$(controller control "$ip" "$agent" control --renderer "http://$ip:8000" --user-agent "$agent" --uri "$url")
  while IFS= read -r result; do line "$result"; done <<< "$output"
}

if [ "$do_unit" = 1 ]; then
  sync_source; unit_tests
fi
if [ "$do_proof" = 1 ]; then
  [ "$do_unit" = 1 ] || sync_source
  build_jar
  if [ -n "$JAR" ] && assemble_home "$JAR" && fixtures && start_server && start_renderers; then
    if [ "$only_pc" = 1 ]; then
      proof_pc
    else
      proof_cases
      proof_controls
      proof_pc
      log_checks
    fi
  fi
fi

if [ "$failures" -eq 0 ]; then echo "RESULT: every line passed"; exit 0; fi
echo "RESULT: $failures line(s) failed"; exit 1
