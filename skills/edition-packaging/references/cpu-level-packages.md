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
