# Rebuilding deb-multimedia's FFmpeg as ours

**For whoever adds an FFmpeg fix to the edition's package.** The players link against deb-multimedia's FFmpeg (epoch 10, `10:9.0.2-dmo1`), so the edition's FFmpeg is that source package plus patches, versioned `10:9.0.2-dmo1+stereo3dN` and sealed `+lc1`.
Each step below was run for `+stereo3d12` (FFmpeg pull requests 25409 and 25377 on top of the `frame_packing` series of 25395); the traps are the ones met there.

## The recipe, short

1. **Search upstream first.** Open and merged pull requests on code.ffmpeg.org for the file and function, then master's log on the file. Ask the Forgejo API for the pull request's current head and commits, because a head moves after a review: `curl -s https://code.ffmpeg.org/api/v1/repos/FFmpeg/FFmpeg/pulls/N` (`head.sha`) and `.../pulls/N/commits`. Fetch the series with `https://code.ffmpeg.org/FFmpeg/FFmpeg/pulls/N.patch` into a folder you name with `-o`.
2. **The plain tree is the base, not the last staged `+lc1` source.** Unpack the published `+lc1` source without applying its patches, then undo Lean Code: `dpkg-source --no-copy --skip-patches -x PUBLISHED.dsc plain` and `python3 sparky-os/repo/plain-from-lc.py plain`. Upstream is then pristine, `debian/patches` holds the published series, the changelog starts at the plain version.
3. **Port on a git tree with the whole series applied.** Copy `plain`, apply `debian/patches/series` in order with `patch -p1 -s -F0`, `git init`, commit. Apply the pull request's commits one at a time with `git apply`, one commit each, messages taken from the pull request (`git mailinfo`). Where a hunk does not apply, change only the context (the neighbouring lines) and keep the added lines as the pull request has them; say what differs in the patch header.
4. **Red and green on the plain source tree.** Two worktrees: red = the ported tree with the fixed source files checked out from the base commit (`git checkout BASE -- file.c`), green = the ported tree. Small configuration in a container, then the new FATE entries: red must fail with the output the fix changes, green must pass; run the neighbouring entries (`fate-filter-stereo3d`, `fate-cbs`) in both and compare.
5. **Recipe folder** `sparky-os/media/ffmpeg/stereo3dN/`: `patches/` (the whole series, DEP-3 headers: `Origin: other, <fork commit URL>`, `Forwarded: <pull request URL>`, `Author`, `Last-Update`), `patches/series`, `changelog.entry` (`@VERSION@`, `@DATE@`), `README.md`. Check that the recipe's series applied to the plain tree with `-F0` gives exactly the ported tree (`diff -r -x debian`).
6. **Source:** `sparky-os/packages/ffmpeg-dmo/make-source.py PLAIN ORIG OUT`. The date comes from the recipe commit (ORDER 421), so commit the recipe first, make the source twice under different `TZ` and `umask`, and compare the sums; they must be identical.
7. **Build** both architectures from the one `.dsc` in the baked build image (`dpkg-buildpackage -b` for amd64, `-B` for i386), with `sparky_provenance_init`; the record must say `recipeDirty False` and an empty `unrecorded`. The Build-Depends of a patch-only version equal the previous version's, so the previous image can be reused.
8. **Checks:** the new FATE entries inside the package build tree of each architecture; the link and start gate on the archives (`lean.release check-link`); exported symbols of the seven libraries equal to the previous version's (`nm -D --defined-only | sort | sha256sum`); the upgrade proof from the published version and from the previous staged one (apt's `Inst`/`Remv` lines, `dpkg --audit`, `dpkg -V`).
9. **Stage** `amd64/`, `i386/`, `source/`, `SHA256SUMS`; publishing is a separate step.

## Traps

| Symptom | Cause | Fix, and how it was found |
|---|---|---|
| `dpkg-source -b` stops with "unexpected upstream changes" after an overlay | `lc-successor.py --in-place --overlay` keeps the old patched upstream tree; a replaced patch no longer matches it | Build from the plain tree with `make-source.py`. Found by the error text of `dpkg-source -b`; the same limit is in the script's own docstring. |
| `git apply --check` fails on the second commit of a pull request | The check runs against the tree without the first commit | Apply commit by commit; check only the first. The message names the hunk of the file that the first commit changes. |
| A Makefile or `tests/fate/*.mak` hunk fails with "patch does not apply" | The pull request's context names lines (`hw_base_encode`, `enc-recon`) that 9.0.2 does not have | Insert the same lines at the same relative place by hand. Compare `git diff` of the port with the pull request's diff; only context lines may differ. |
| The pull request's head is not the one in the evidence of an earlier lane | The author pushed again (a third commit, 2026-11-06) | Read the head from the API on the day, fetch `N.patch`, and compare diff bodies ignoring `index` lines and the trailing git version line. |
| Two FATE entries fail in both red and green | The fate-suite folder lacks their sample (`Error opening input file /fate-suite/h264/depth-sei.h264` in the `.err` file) | Open `tests/data/fate/NAME.err` of the failing entry before counting it; a failure that is identical in red and green and names a missing file is not the change. |
| Two sources of the same commit differ in the changelog trailer and the tar times | The clock, zone, umask or checkout time reached the bytes | `reproducible.py` (ORDER 421): recipe-commit date, `TZ=UTC`, normalised modes. Prove it by making the source under two zones and umasks. |
| `curl -o` or `>` wrote a file into the wrong folder | A `cd` before it had failed and the command went on | Give every download an absolute `-o` path, and start such a line with `set -e` or `cd ... || exit`. |
| `sha256sum -c` shows no "OK" and a count of non-OK lines is 62 | The check prints its words in the station's language ("SUCESSO") | Count with `LC_ALL=C sha256sum -c SHA256SUMS \| grep -vc ': OK$'`. Found by reading the first lines of the output instead of trusting the count. |
| The upgrade proof upgrades more than FFmpeg | `apt-get dist-upgrade` in a fresh testing container also takes testing's newer packages | Read the `Inst` and `Remv` lines: the proof is zero `Remv`/`Purg`, `dpkg --audit` empty, `dpkg -V` clean, and the players still installable (simulated). Run it twice, from the published version and from the previous staged one (install that one first from its stage as a local repository, pinned 1002). |
| A container command ran as the wrong user and left root-owned files | No `--user` | Run test containers with `--user $(id -u):$(id -g)`; build containers chown their work folder in a `trap ... EXIT`. |

## Perks

- The FATE entries of a patch-only version can run in the package's own build tree (shared libraries through `LD_LIBRARY_PATH`), so the proof is of the binaries that ship.
- The H.264 clause for the SEI header the 25409 patch bounds is 7.3.2.3.1 (`last_payload_type_byte`, `last_payload_size_byte`; H.264 V16, 06/2026, printed page 50).
