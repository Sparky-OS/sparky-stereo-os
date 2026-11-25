#!/bin/bash
# A core limit of exactly 1 suppresses the piped core helper; a zero limit does not.
# build-script-packages.sh TREE OUT IMAGE RECIPE...: one clean build of each script package of the build tree (Paweł's
# formula, lean.standalone), each in its own container from IMAGE, then lean.release check-debs (the build record).
# The provenance comes from the tree's commit (sparky_provenance_init); a dirty tree is recorded as dirty.
# Environment: DOCKER_HOST, CONTAINER_IDS.
set -euo pipefail
TREE=$(cd "${1:?build tree}" && pwd); OUT=$(mkdir -p "${2:?output}" && cd "$2" && pwd); IMAGE=${3:?image}; shift 3
: "${CONTAINER_IDS:?}"
. "$TREE/sparky-os/repo/build-provenance.sh"
for recipe in "$@"; do
	dir=$TREE/sparky-os/packages/$recipe
	[ -f "$dir/build.sh" ] || { echo "no recipe $dir" >&2; exit 1; }
	sparky_provenance_init "$IMAGE" "$dir"
	mkdir -p "$OUT/$recipe"
	name=kw63-build-$recipe-$$
	docker create --name "$name" --ulimit core=1 --network none --cpus 4 --platform linux/amd64 --user "$(id -u):$(id -g)" \
		"${SPARKY_PROV_ARGS[@]}" -e HOME=/out/home -e TMPDIR=/out/tmp -e OUT=/out \
		--mount "type=bind,src=$TREE,dst=/tree,readonly" --mount "type=bind,src=$OUT/$recipe,dst=/out" \
		"$IMAGE" bash -c 'set -e; mkdir -p /out/home /out/tmp; git config --global --add safe.directory /tree; bash /tree/sparky-os/packages/'"$recipe"'/build.sh > /out/build.log 2>&1; cd /out; PYTHONPATH=/tree/sparky-os python3 -m lean.release check-debs /out/*+lc1_all.deb >> /out/build.log 2>&1; rm -rf /out/home /out/tmp' > /dev/null
	docker inspect -f '{{.Id}}' "$name" >> "$CONTAINER_IDS"
	status=0; docker start -a "$name" || status=$?
	docker rm -f "$name" > /dev/null
	echo "$recipe: exit $status"; tail -3 "$OUT/$recipe/build.log"
	[ "$status" = 0 ] || exit "$status"
done
