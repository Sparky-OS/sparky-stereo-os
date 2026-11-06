# Reproducible sources: the recipe date, the real clean, and how to compare runs

Written 2026-11-06 from ORDERS 421, 421b and 427 (build tree 77768db9).
The same recipe commit must give the same `.dsc` and `.debian.tar.xz` whatever the clock, the time zone, the umask and the checkout time.
This page is the working recipe, what the real `dpkg-buildpackage` does to a tree, how to prove a route, and the traps met on the way.

## The pattern in five lines

1. The date of a source is its recipe's, never the clock: `SOURCE_DATE_EPOCH`, else the committer date of the last commit that touched the recipe's folder (a clean tree is required), else the tool stops. `sparky-os/repo/reproducible.py epoch RECIPE_DIR` prints it.
2. `sparky_provenance_init IMAGE [RECIPE_DIR]` (`sparky-os/repo/build-provenance.sh`) exports `SOURCE_DATE_EPOCH` and `SOURCE_DATE_RFC2822` and adds them, with `reproducible.py` at `/run/reproducible.py`, to `"${SPARKY_PROV_ARGS[@]}"` for the container.
3. Every changelog entry we write takes the trailer date from `SOURCE_DATE_RFC2822`. `dch` ignores `SOURCE_DATE_EPOCH`, so every `dch` call carries `--date "$SOURCE_DATE_RFC2822"`.
4. Right before each `dpkg-source -b`, `reproducible.py normalize-tree EPOCH TREE` sets the time and mode of `debian/` and of the `debian/source/include-binaries` files; a native source uses `reproducible.py normalize EPOCH TREE` (the whole tree is packed).
5. `lean.debian_prepare` stops when no date reached it.

## What `dpkg-buildpackage -S` changes in the tree (measured, ORDER 427)

Run the real thing on a source: `dpkg-buildpackage -S -d -us -uc` (source only, no binary build, build dependencies not checked). It runs `dpkg-source --before-build`, `debian/rules clean`, `dpkg-source -b`, then writes `.changes` and `.buildinfo`.
The image needs what `clean` calls: `debhelper`, `pkg-kde-tools` (it provides `dh-sequence-kf6`, `-plasma`, `-qmldeps` and `-pkgkde-symbolshelper`), `cmake` and `extra-cmake-modules` for the Qt and Plasma sources.
Measured on Debian's qt6-declarative 6.11.2+dfsg-3, plasma-nm 6.7.4-2, kwin, dpkg-stereo and the kernel libc-dev-cross source:
- the only new file is `debian/files`;
- no file of `debian/` changes in content, mode or time;
- `dh_clean` deletes files whose names end in `#` (qt6-declarative's tests/auto/qml/ecmascripttests/test262/.../`#undefined-tobigint.js#` is in the upstream tarball); `dpkg-source -b` then says `ignoring deletion of file ..., use --include-removal to override` and packs the file anyway, so the source keeps it;
- the lc source's `clean` also runs `lean.source_tree restore` and `rm -rf .sparky-lc`; both left the packed bytes equal to the published ones.
`debian/rules clean` therefore does not make a source differ between runs, but only a run of the real command shows that; a shim that skips it proves nothing about it.

## The proof of one route

Three runs from fresh clones of one commit, with three clocks, zones, umasks and checkout times, in a container with `--network none` (libfaketime, `NO_FAKE_STAT=1`, `FAKETIME_DONT_RESET=1`):

| run | clock | zone | umask | files touched at |
|---|---|---|---|---|
| A | 2026-11-06 11:00 | America/Sao_Paulo | 022 | 2026-11-06 10:00 |
| B | 2026-11-20 03:30 | Asia/Tokyo | 077 | 2026-11-19 01:00 |
| C | 2027-03-01 23:59:50 | Pacific/Auckland | 002 | 2025-01-01 |

Compare `sha256sum` of every `.dsc` and every `.tar.*` that is not an `.orig`. Green is the same list of sums in all three.
A second generation catches what the route's own pack hides: `dpkg-source -x` the result, `dpkg-buildpackage -S` it again, and compare.
Normalize the extracted tree first (as the producers do) or the second generation differs by umask alone, see the traps.

To compare with a published or staged source, extract both with `dpkg-source --no-check -x` and `diff -rq` the trees. Expected differences only: the changelog trailer dates, and the bundled `debian/sparky-lean-toolkit` (the new tree's toolkit is newer than the published one's). Anything else is a finding.

## Traps (symptom, cause, fix, how it was found)

- **A dry run that skips `debian/rules clean` proves nothing about it.** Symptom: ORDER 421b's routes were green and "no script ran on the real Debian and published inputs". Cause: its `dpkg-buildpackage` shim called `dpkg-source -b` directly. Fix: shim `dpkg-buildpackage` as `exec /usr/bin/dpkg-buildpackage -S -d -us -uc` and put the clean helpers in the image. Found by reading the shim.
- **`dpkg-source -x` follows the umask.** Symptom: a second-generation source differs between runs only in the tar member modes (`drwx------` in the umask 077 run). Cause: the extracted tree keeps the extracting umask and `dpkg-source -b` packs modes as found. Fix: `normalize-tree` (or `normalize` for native) between `-x` and the next `-b`, which every producer already does. Found by `tar -tvf` of the two `.debian.tar.xz` files and `diff`.
- **A comparison of zero files says "identical".** Symptom: `identical (0 files)` for a second generation that had failed. Cause: the sums list was empty on both sides; the failure was `cd` into a relative path inside a subshell after the first `cd`. Fix: an empty list is a failure (`NO FILES`), and the script's own failure line is printed. Found by reading the run's `gen2.out`, whose last line was `gen2 FAILED`.
- **`set -e -o pipefail` ends a script at a `diff | grep | head`.** Symptom: the second pass of a loop never started, no error text. Cause: `diff` exits 1 on a difference, which is the result of the pipeline. Fix: `|| true` on a pipeline whose failure is the information. Found by the missing output directory of the second pass.
- **libfaketime shifts `stat()` too.** Symptom: checkout times seemed to follow the fake clock. Fix: `NO_FAKE_STAT=1` (ORDER 421). A tar that extracts a member dated after the fake clock prints `time stamp ... is N s in the future`: harmless, the recipe date can be later than the faked now.
- **`eval exec python3 $script` breaks on a quoted argument.** Symptom: `syntax error near unexpected token '('` in the log. Fix: build the command with `printf '%q '` and run it without `eval`.
- **A route's input must be the real one.** `apt-get source --download-only` in a container with `https-only-apt.sh` gives Debian's files; the recipes pin the `.dsc` sha256, so a moved testing fails the pin, which is the right answer. Our own sources are read from the live repository's resolved copy (`/var/tmp/sparky-repo-current`, its InRelease equal to the live one), read only and never hard-linked.
- **Pick scratch that cannot cross a disk floor.** The runs write 0.3 to 0.6 GB each; `/dev/shm` held them with no disk floor in play. Outputs are small and go into the lane's evidence.
- **A transition rebuild of a source with a preserve plan needs the plan.** The `transition-rebuilds` route with no `PLAIN_OPTIONS` turned the published qt6-declarative +stereo3d1+lc1 into a +stereo3d2+lc1 without `debian/sparky-lean-preserve.json` (the published one has it). Reproducible, but not the same content: give the option the source's shape needs, or use `lc-successor.py`, which keeps the plan.

## Commands

```
# Debian's real source, in a container with https-only apt (the CA bundle mounted read only)
apt-get source --download-only qt6-declarative        # then check the .dsc sha256 the recipe pins
# one run: the route's own script, the clock and zone moved, the umask set inside, no network
docker run --rm --ulimit core=0 --network none --user 1000:1000 "${SPARKY_PROV_ARGS[@]}" \
  -e TZ=Asia/Tokyo -e LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1 \
  -e FAKETIME='@2026-11-20 03:30:00' -e FAKETIME_DONT_RESET=1 -e NO_FAKE_STAT=1 IMAGE \
  bash -c 'umask 077; exec bash ROUTE-SCRIPT'
# compare a result with the published source (expected: trailer dates and the bundled toolkit only)
dpkg-source --no-check -x NEW.dsc new; dpkg-source --no-check -x PUBLISHED.dsc old; diff -rq old new
```

A negative control keeps the check honest: the same route at a commit before the producer was converted (build main 7822d95d for the qt6-declarative route) gives different bytes, and the difference is the clock in the changelog trailer.

## Routes proven on real inputs (ORDER 427)

See the lane report for the sums. Patterns covered: a `build-in-container.sh` (qt6-declarative from Debian's source), a host `dch` recipe (plasma-nm), a transition rebuild, `lc-successor.py` on a published source, a prepare script with `include-binaries` (kwin), a native package (dpkg-stereo `build-source.sh`) and a generated native source (kernel libc-dev-cross). Mesa's `prepare-source.sh` could not be run on real input: its +stereo3d16+lc1 input is on no disk except a slice without archives.
