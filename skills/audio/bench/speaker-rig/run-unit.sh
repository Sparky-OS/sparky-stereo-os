#!/bin/bash
# run-unit.sh SRC_DIR(plasma-pa) [TEST] [SOURCE] : builds and runs a QtTest against Qt's core only, in a container with no network.
# Needs DOCKER_HOST, UNIT_OUT (a world-writable scratch folder) and UNIT_IMAGE (g++, qt6-base-dev, qt6-base-dev-tools).
set -euo pipefail
: "${DOCKER_HOST:?the lane socket}"
SRC=$1; T=${2:-speakersetupconftest}
docker rm -f unit-run >/dev/null 2>&1 || true
docker run --rm --name unit-run --pull=never --network none --ulimit core=0 --cpus 2 -v "$SRC":/src:ro -v "${UNIT_OUT:?}":/out "${UNIT_IMAGE:?an image with g++ and qt6-base-dev, qt6-base-dev-tools}" sh -c '
set -e; cd /out; rm -rf b; mkdir b; cd b
F="-fPIC -std=c++20 -I/usr/include/x86_64-linux-gnu/qt6 -I/usr/include/x86_64-linux-gnu/qt6/QtCore -I/usr/include/x86_64-linux-gnu/qt6/QtTest"
/usr/lib/qt6/libexec/moc /src/autotests/'$T'.cpp -o '$T'.moc -I/src/src
g++ -O1 -Wall $F -I/src/src -I. -o t /src/autotests/'$T'.cpp /src/src/'${3:-speakersetupconf}'.cpp -lQt6Test -lQt6Core
ulimit -c 0
QT_QPA_PLATFORM=offscreen ./t'
