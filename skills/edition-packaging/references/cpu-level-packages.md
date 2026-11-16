# Packages built for the processor's level (x86-64-v3)

How the edition gives a processor the build made for it, and what each mechanism can and cannot do on a Debian forky base.
The edition's level is x86-64-v3, chosen by the machine and never by a question; the baseline always stays installed and bootable, optimised parts only add to it.

## The recipe: apt architecture variants (sparky-stereo-apt 20261116.1)

1. `/etc/apt/apt.conf.d/62sparky-stereo-variants` sets `APT::Architecture-Variants "auto";` and `Dir::dpkg::varianttable` to the package's own table, `/usr/share/sparky-stereo-apt/varianttable`.
2. The table has one row, the `amd64v3` row of apt's own `test/integration/varianttable` (apt 3.3.7). apt enables a variant when `/proc/cpuinfo` has every flag of its row, at every run.
3. The repository lists `amd64v3` in `Architectures:` of its Release file and carries `main/binary-amd64v3/Packages` as a **complete copy**: the rebuilt packages plus every baseline package. Each v3 build is `Architecture: amd64` with an extra `Architecture-Variant: amd64v3` field.
4. Proof: `tests/variants/run.sh PUBLISHED_DEB WORK` in the package folder (amd64 `debian:testing` container, toy repositories, no network except the Debian-repository case). Expect one red line (the published package gives the baseline build on a v3 processor) and then PASS on v3, v2, baseline processor, opt-out, incomplete-index control and Debian untouched. Exit 0 means the red failed and every green passed.
5. The person turns it off with `APT::Architecture-Variants "";` in a file that sorts after 62.

## The hardware layer's two parts (sparky-stereo-hardware 0.1.29)

1. **The v3 kernel by detection.** `lib/detect.py` adds `linux-image-sparky-stereo-v3` and `linux-headers-sparky-stereo-v3` to the plan when the loader lists `x86-64-v3 (supported, searched)` on amd64; `sparky-stereo-hardware --auto` installs them with apt. The baseline kernel is never removed, so GRUB lists both. Which boots first: `/etc/grub.d/10_linux` sorts releases with `version_sort -r`, and `7.3.1-stereo3d16-v3` sorts above `7.3.1-stereo3d16` and `7.3.1-rt-stereo3d16`. The newest build number wins over the flavour, so v3 stays on top only while a round publishes the flavours together. `--kernel base` is the person's choice (a mark file; nothing installed is removed), `--kernel v3` undoes it. Proof: `tests/detection.py` (the plan for v3, v2, baseline, arm64, chosen baseline), `tests/kernel-v3.sh` (GRUB's own sort code, the published metas, installing removes nothing).
2. **The guard for a package built above the processor.** `variant-check` reads the loader's levels and `dpkg-query -W -f '${db:Status-Abbrev}\t${Package}\t${Architecture-Variant}'` (dpkg keeps the unknown field), keeps one notice in the problems engine (`variant-mismatch`, ten languages) with the Repair `sparky-stereo-hardware --variants`, which updates the lists (apt picks its index by the processor it runs on), reinstalls those packages so apt takes the baseline build, and clears the notice. It runs after every dpkg run (the post-invoke hook looks first for the field in the status file) and at boot. Proof: `tests/variant-check.sh`: a variant installed by apt on a faked v3 processor, the processor faked down (`/proc/cpuinfo` bind-mounted for apt, `GLIBC_TUNABLES=glibc.cpu.hwcaps=-AVX2` for the loader), notice, Repair, notice ended.

## The repository side (publish-tree.sh)

A variant build is `NAME_VERSION_amd64v3.deb`, control `Architecture: amd64` plus `Architecture-Variant: amd64v3`. `publish-tree.sh` selects it under the variant's own name, leaves it out of `binary-amd64`, Contents and the link gate, and writes `binary-amd64v3/Packages` as every baseline `amd64` record with the variant builds in place of theirs, and `amd64v3` in Release `Architectures:`. A tree with no variant build is byte-identical to before. Test: `sparky-os/repo/tests/variants/run.sh` (throwaway tree and key; the Lean Code gates are stubbed in the test's copy only).

## The round's other tools on a tree with an amd64v3 index (milestone 3)

Each was run on the throwaway tree of `sparky-os/repo/tests/variants` (the real `publish-tree.sh`, Lean Code gates stubbed in the test's copy), red against main's tool, green with the change:

| Tool | What it did with `binary-amd64v3` | The change |
| --- | --- | --- |
| `repo/check-installable.py` | read it as an architecture of its own (both the unsigned glob and the signed Release rows) | skip `binary-*v[2-4]`: the baseline index is the complete one with the same dependencies |
| `release/check-repository-dependencies.py` | a staged `_amd64v3.deb` replaced the baseline build of the same name in its rehearsal index | skip rows and archives named `_amd64v3.deb` |
| `release/make-sbom.py` | one purl for two builds | `arch=` is the variant for a variant |
| `release/supply_chain.py`, `verify-online-repository.py` | keyed by Filename, rows read from Release | none (the Release loop proven offline) |
| `release/stage-final-repository.py` | "Conflicting binary identity" for a variant | the variant is the architecture of the identity (not run: the tool needs the round's notes) |
| `lean.release check-debs` / `check-repo` | "duplicate package identity" for a variant and its baseline twin | the key is (package, version, architecture:variant) and the `-lc-hr` companion must carry the same variant (`tests/cpu-level/pairing.sh`) |

Cost of the pairing: a variant build of a package with a companion needs both archives marked, and a variant set can be checked alone or with its baseline.

## Writing the variant at build time

`XB-Architecture-Variant: amd64v3` in each binary stanza of `debian/control` reaches the control file of every package through `dpkg-gencontrol` (checked: both `libstereo-av1` and `libstereo-av-dev`), with `debian/rules` untouched. But **the Lean Code link and start gate then fails with "archive attempted to substitute supplied NAME"**: its local index lists the supplied package with the field and apt ignores a variant that its Release does not declare, so the solver takes the published baseline build. Until `lean/archive.py` leaves the field out of that index (a toolkit release: the code hash and the version table change), the field is added after the gate by a repack of the control file, as the milestone 2 test does.

## Building a native script package the way a round accepts it

1. `build.sh` of the recipe (lean.standalone) makes the retained source package (`.dsc`, `.tar.xz`); then `dpkg-source -x`, `apt-get build-dep` and `dpkg-buildpackage -us -uc -b` build it again; then `python3 -m lean.release check-debs` writes the record.
2. The record needs the host's facts: on the host `. repo/build-provenance.sh; sparky_provenance_init IMAGE RECIPE_DIR` and the container gets `"${SPARKY_PROV_ARGS[@]}"`. Without them check-debs stops: "the build script did not call sparky_provenance_init". Commit everything first: the record says `recipeDirty` otherwise.
3. For the archive link and start gate (`SPARKY_LC_ARCHIVE_CONFIG` and `SPARKY_LC_SCRATCH`, bubblewrap, the three `--security-opt` flags, `ca-certificates` installed in the container) the sources must be the ones the package's dependencies live in: Debian `main non-free non-free-firmware`, deb-multimedia, **SparkyLinux's core and tiamat** (sparky-remsu, sparky-xterm), and the published tree as a `file:` archive. A missing one shows as "none of the choices are installable"; a container without `ca-certificates` shows as "certificate verify failed" inside the gate's isolated apt.
4. The upgrade proof reads apt's lines: install the published version, then `apt-get -s install ./NEW.deb` and count `Remv`.

## What forky does today (measured 2026-11-16, `debian:testing` of 2026-10-27)

| Fact | Result |
|---|---|
| apt | 3.3.7; `libapt-pkg` knows `APT::Architecture-Variants` and `Dir::dpkg::varianttable` |
| dpkg | 1.23.11; `/usr/share/dpkg` holds abitable, cputable, ostable, tupletable and **no varianttable** |
| `auto` without a table | does nothing: the baseline build stays the candidate |
| `ld.so --help` | lists `x86-64-v3 (supported, searched)` on a v3 processor; the same test CachyOS's `cachyos-repo.sh` makes |

## Traps

- **"auto" does nothing and says nothing.** Symptom: `Architecture-Variants "auto"` set, a v3 index published, apt still installs the baseline. Cause: no `varianttable` file (forky's dpkg ships none). Fix: ship a table and point `Dir::dpkg::varianttable` at it (our own path, so a dpkg that ships one later does not collide). Found by running the toy repository with and without the file; the mutation (conf without the table) gives the baseline again.
- **A variant index supplants the baseline index of the whole repository.** Symptom: after publishing `amd64v3`, a package that has no v3 build vanishes from `apt-cache policy` ("Unable to locate package"). Cause: apt takes the variant index instead of the baseline one, in every component. Fix: the v3 index lists everything. The test keeps the incomplete index as a control.
- **apt acts only when it runs.** A v3 build that stays installed on a disk moved to an older processor is not checked; it stays as installed until apt installs that package again, and the processor may refuse an instruction. The hardware layer's `cpu-level` fact is what a check for this reads (not built yet).
- **Variants do nothing for Debian's packages.** Debian's repository has no `amd64v3` index; only what our repository rebuilds benefits. Rebuilding Debian packages at v3 (what PikaOS and CachyOS do) is a separate decision about each package.
- **glibc-hwcaps is the other mechanism and is safe across processors.** A shared library built again with `-march=x86-64-v3` goes in `/usr/lib/x86_64-linux-gnu/glibc-hwcaps/x86-64-v3/`; the loader picks it at run time and falls back to the baseline file by itself. It covers libraries only, not executables or the kernel.
- **The v3 kernel is a flavour, not a variant.** `linux-image-sparky-stereo-v3` (config `CONFIG_X86_64_VERSION=3`) is published beside the baseline kernel; the ISO installs the baseline one, so nothing selects the v3 kernel from `cpu-level` yet.

- **dpkg-scanpackages takes files named `*_ARCH.deb`.** Symptom: the variant index lacked the variant build, only baseline packages. Cause: `dpkg-scanpackages --arch amd64` skips `_amd64v3.deb`. Fix: scan `--arch amd64v3` for the variants and `--arch amd64` for the rest, merge. Found by the first run of the repository test.
- **Two builds with one name, version and architecture share an identity.** The script of main stops with "conflicting archives" on a variant build; a variant named `NAME_VERSION_amd64.deb` would also take the baseline's pool path. The selection refuses it by name.
- **A container's `ld.so --help` ignores `/proc/cpuinfo`.** The loader reads CPUID, apt reads `/proc/cpuinfo`: fake both (a bind mount for apt, `GLIBC_TUNABLES=glibc.cpu.hwcaps=-AVX2` for the loader), or the guard and apt disagree.
- **lintian `uses-dpkg-database-directly`.** A script that opens the dpkg status file adds a lintian line against the published baseline; ask `dpkg-query` for the field instead.

## Where the facts come from

`sparky-stereo-hardware` prints `fact cpu-level` and `fact x86-64-v3` from the loader's own list (`lib/detect.py`, comments name the sources); apt reads `/proc/cpuinfo` itself, so the two can disagree and the tool prints a disagreement line instead of hiding it.

## Credits

The APT team (architecture variants, the table format); Canonical (amd64v3 in Ubuntu 25.10); openSUSE (glibc-hwcaps pattern packages); CachyOS (`cachyos-repo.sh`'s level detection, the levelled repositories); PikaOS (Debian sources rebuilt at x86-64-v3). Names from each project's own pages.
