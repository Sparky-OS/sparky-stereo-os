#!/bin/bash
# Builds ums-proof-rygel:1, the PC as a renderer (Rygel's MPRIS plugin and an MPRIS2 player). Needs the network once, for apt over https.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SCR=${UMS_PROOF_SCRATCH:?set UMS_PROOF_SCRATCH}
: "${BASE_IMAGE:?set BASE_IMAGE to a pinned Debian testing image}"
: "${HTTPS_ONLY_APT:?set HTTPS_ONLY_APT to a script that makes apt refuse plain http}"
context=$SCR/rygel-context
mkdir -p "$context"
cp "$HERE/Dockerfile" "$HERE/pc-renderer.sh" "$HERE/pc-probe.sh" "$context/"
cp "$HTTPS_ONLY_APT" "$context/https-only-apt.sh"
sed -i "s#^FROM .*#FROM $BASE_IMAGE#" "$context/Dockerfile"
cp /etc/ssl/certs/ca-certificates.crt "$context/ca-certificates.crt"
sed -i 's#source=/etc/ssl/certs/ca-certificates.crt#source=ca-certificates.crt#' "$context/Dockerfile"
docker build --network default -t ums-proof-rygel:1 "$context"
