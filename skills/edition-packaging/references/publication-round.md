# A publication round: frozen tree, pre-round checks, upgrade proof, reading a failure

**For the maintainer who turns accepted packages into one signed repository state.**
The round's scripts take a build-repository commit, check it, build the new tree from the accepted packages, prove that an installed edition upgrades to it, and stop on the first failure.
Written on 2026-11-06 from the rehearsal described under "Rehearse before the real round"; the machinery is the round folder's `official-part1.sh`, `pre-round-checks.sh`, `round-worktree.sh` and `run-proofs.sh` with its `proof-scripts/`.

## The recipe

1. **Freeze the build tree.** `round-worktree.sh WORKTREE [COMMIT]` makes (or reuses) a git worktree of the build repository at one commit; the default commit is `origin/main` as fetched now.
   Every build-repository path of the round (`publish-tree.sh`, the lean toolkit, the supply-chain tools, the pre-round checks) points into that worktree, never into the shared checkout, because branches are merged into the shared checkout while a round runs for hours.
   It prints `round-commit <40 hex> <path>`; the round log, `round-commit.txt` and the supply-chain file `round-toolkit-ROUND.json` (listed in `SHA256SUMS`, so the detached signature covers it) name that commit.
   An existing worktree is reused only at exactly that commit and with nothing changed; any other state stops with the reason.
   Remove it when the round is published: `git worktree remove --force WORKTREE`.
2. **Pass the pre-round checks.** `pre-round-checks.sh WORKTREE OUTDIR` runs, each in its own container (image `lc-linebreak-rebuilds-311-test:1`, `--ulimit core=0`, `--network none`, the three `--security-opt` options `seccomp=unconfined apparmor=unconfined systempaths=unconfined` that the link-gate tests need for bubblewrap), the whole lean suite (`python3 -m pytest lean/tests`: 461 passed, 30 skipped on 2026-11-06, 4 to 5 minutes), `tests/reproducible-sources/test.sh` and `tests/supply-chain/test-wiring.sh`.
   It runs all three even after a failure, prints one PASS or FAIL line each, and exits 1 if any did not pass; `official-part1.sh` stops there, before it copies anything.
3. **Build the tree** (`official-part1.sh`: base check, source forest, destination with the pool hard-linked from the base, `publish-tree.sh`, supply chain). Nothing is signed with a key the script was not given, and nothing is sent.
4. **Prove the upgrade on the edition's own dpkg.** `run-proofs.sh ROUND BASE DEST "a b e"`; case `e` installs the live set's `dpkg` and `dpkg-stereo` first, shows `dpkg --version` and `dpkg-query -W dpkg`, installs the package set under that dpkg, then runs `apt-get dist-upgrade` to the new tree and judges it on apt's own `Inst` and `Remv` lines (below).
   A stock-dpkg proof can pass where the edition's dpkg refuses (a shared Multi-Arch file that dpkg-stereo projected, ORDER 363).

## What the upgrade proof (case e) fails on

- the simulated `Inst dpkg` line is not the edition's (`+stereo` in the version): the proof would run on Debian's dpkg;
- the `dpkg` in the database after the base install, or after the upgrade, is not `+stereo`, does not Provide `dpkg-lean-code`, or `dpkg-stereo` is not installed;
- the dist-upgrade installs nothing: no `Inst` line in the simulation (`apt-get -s`), no `Unpacking` line in the real run (a real apt run prints no `Inst` or `Remv` lines; dpkg's `Unpacking` and `Removing` lines are their counterparts), so it proves nothing;
- anything is kept back;
- apt removes a package (`Remv` line in the simulation, `Removing` line in the real run) that `proof-scripts/e-allowed-remv.txt` does not list (one name per line, a reason after it; the default is none; a round that must remove something names it and why);
- a planted conffile edit is gone after the upgrade: before the real upgrade the proof appends a marker line to an on-disk conffile of up to 40 packages the upgrade touches (a person's edit), and after it the marker must still be there;
- a second `dist-upgrade` simulation would still change something; `dpkg --audit` is not empty; `dpkg-stereo --verify` or `--verify --deep` is not clean.

The case's verdict is `OUT/e/verdict.txt` (`PASS (n checks)` or the first `FAIL ...`); `run-proofs.sh` exits 1 when any case's container failed or case e's verdict is not PASS.
`proof-scripts/test-checks.sh` runs every check on planted logs, red and green, in a container: run it after changing `proof-checks.sh`.
Environment for a small rehearsal: `E_PACKAGES` (default the user meta and both developer tasks), `E_I386=0`, `E_ALLOWED_REMV`, `RUN_PROOFS_MIN_MIB` (the disk floor for one case, default 28 GiB because a full case writes about 12 GiB under Docker's root), `PROOF_OUT`, `PROOF_SCRIPTS`.

## Every binary keeps its source

Run the build tree's `sparky-os/repo/check-binary-sources.py` on the finished repository immediately after `publish-tree.sh` succeeds, before the supply-chain step and before authorizing Part 2:

```sh
python3 "$BUILD/sparky-os/repo/check-binary-sources.py" "$DEST" \
    --table "$ROUND_WORK/binary-sources.tsv" > "$ROUND_WORK/binary-sources.log" 2>&1
```

Propagate its exit status: 0 means every indexed binary has its matching source; 1 names every binary whose source is missing or incomplete; 2 means the gate could not check, and also refuses the round.
Print the failure log before stopping.
Keep the table and log with the round's evidence.

The check reads every suite and architecture, including `binary-all`, taking the source name and optional source version from the binary's `Source` field.
An omitted source name means the binary's own package name; an omitted source version means its binary version, as [Debian Policy 5.6.1](https://www.debian.org/doc/debian-policy/ch-controlfields.html#source) specifies.
An explicit source version takes precedence, including for a binary-only rebuild.
The matching `Sources` record in that suite must name a real `.dsc` with the recorded SHA-256 and size, the right source name and version, and the same source components as the descriptor.
Every component must exist with the recorded size.
This is a completeness check; it does not rehash the large component archives or establish that a replacement source produced an existing binary.

Before accepting the gate, run it on a copy of the live indexes that lacks the affected sources and require exit 1 naming those binaries.
After adding genuine, proved source packages and regenerating `Sources`, repeat on that tree and require exit 0.
Keep independent positive and negative fixtures for an explicit source version, compressed-only indexes, a missing descriptor, a missing component and a corrupt descriptor.
Other missing sources must keep the whole-tree verdict red; a kernel-only or synthetic green is labelled with its actual scope.

Trap, found in ORDER 557:

- **Symptom:** the repository retained kernel build 16 binaries but no longer offered their source through `deb-src`, and publication checks had passed.
- **Cause:** the round retired builds 14, 14.2 and 15 with a pattern that also matched their shared `7.3.1.orig.tar.xz` filename.
  A later round starting with build 16 matched that same filename and removed build 16's own orig archives.
  Its descriptors then disappeared from the resulting source index and pool.
- **Fix:** retire only explicit Debian build versions in `old_kernel()`; a filename shared by several builds is never a removal pattern.
  Keep the shared orig while any retained descriptor needs it.
  If an incoming orig has the same name with different bytes, stop on that collision and review the retained source closures before replacing anything.
  Never leave a retained descriptor referring to another build's orig bytes.
  Run the source gate on the completed tree so that this loss cannot pass silently again.
- **How found:** reconcile `Packages` against `Sources` and the actual pool, then compare the round's `kernel-left-pool.txt` with `old_kernel()`.
  The log named all three build-16 orig files even though the comment described only older builds.

A restoration must preserve its evidence too.
Use the exact historical recipe and the published build records, not the current recipe with a new date.
Two regenerated archives being equal proves repeatability; compare their hashes with the recorded source hashes separately.
For a byte-for-byte restoration, a different recorded hash stops staging that replacement.
If the original archives are lost and corresponding-source regeneration is explicitly requested, follow the content proof below and preserve both sets of hashes.
Where no record contains a source hash, label the next-best evidence explicitly, such as a matching retained Git tree, patch hashes, configuration and embedded recipe.
Never relabel an unproved replacement as the source of a published binary.

## A source restored after its archives were lost

An original archive hash and the content needed to rebuild its binary answer different questions.
When the original archives have been removed and cannot be recovered, say so; a regenerated archive never claims their hashes.
For a requested corresponding-source restoration, keep this evidence beside the stage:

1. Recover the historical recipe commit, upstream revision, patch list and patch hashes from the retained build records.
   Reconstruct each flavour and compare its Git tree with the accepted tree; record an ISA-specific tree separately when it differs.
2. Read the actual published packages.
   Recover their changelog, copyright and final configuration verbatim, not a newly dated equivalent.
   Retain compressed records as well as their decoded source inputs when compression is part of the file being compared.
   Keep a file-by-file table with package name, installed/control path, corresponding source path, SHA-256 and comparison result.
   Distinguish restored recipe inputs from retained binary packaging records; a captured control file is evidence of that binary's metadata, not a claim that a source control template has the same format.
3. Preserve the historical build scripts and configuration fragments, and carry the exact published final configuration with them.
   Stop an affected flavour on a content difference and retain its diff.
   Do not rebuild or re-sign the kernel as part of a source-only restoration.
4. Normalize the archive through the reproducible-source route: a fixed recipe epoch, sorted members, normalized times and modes, numeric root owners, and normalized `debian/` plus `include-binaries` inputs before `dpkg-source -b`.
   Normalize the entire orig tree too, after applying patches: a restrictive umask can leave a patched file at 0600 while its Git identity still matches 100644.
   Independently inspect the final archive's owners, times, modes and member order, and reconstruct its Git tree from the archived contents.
   Run it twice from fresh disposable source trees with different zones and umasks; require the same three archive hashes per flavour.
5. Write `REGENERATED.txt` in the stage with the regeneration date, historical recipe commit, accepted and reconstructed tree identities, file-comparison results, and both the original recorded and regenerated archive hashes.
   Explain why the archives differ and where the originals were lost.
   Keep `SHA256SUMS` and `.keep`, then run the all-binary source gate on the copied indexes plus every required stage.

This proves the recorded source content and embedded packaging files, together with repeatable replacement archives.
It does not prove the original archive bytes or a repeated binary build.
A metadata fix to a carried binary must also provide its real source package; otherwise the repository gate correctly remains red.

Trap: a historical source preparer used the clock for its changelog and packed incidental file metadata.
Re-running its commit produced a correct accepted Git tree and different archive hashes.
The binary's embedded changelog exposed the changed dates; restoring those bytes and normalizing the archive made the replacement repeatable without pretending it was the removed archive.
The independent archive inspection also caught v3 patch outputs at 0600: two matching hashes alone did not prove normalized modes.

## Reading a failed round

| You see | It means | First look |
|---|---|---|
| `round-worktree: ... is at X, the round's commit is Y` | the worktree of an earlier try is still there | remove it (`git worktree remove --force`) or name its commit |
| `PRE-ROUND CHECKS FAILED` | one of the three checks | `OUTDIR/summary.txt` names it, `OUTDIR/<check>.log` has the output; the lean suite's first `FAILED` line names the test |
| `wiring: ... docker run lacks "${SPARKY_PROV_ARGS[@]}"` | a build driver does not pass the host's provenance facts | the file named on that line |
| `BASE is not live` | the base copy's InRelease hash differs from the server's | someone published since the copy; start from the live tree |
| `supplied input changed after its universe was frozen` | something touched a file of the base or destination pool while the link gate ran (a hard-link copy, a delete); the gate stamps inode, size and change times | never `cp -al`, delete or rename any tree sharing the pool during a run; reads are safe |
| `lc1: release blocked: (...): matching HR documentation package is missing` | a package with the lc1 mark went into the source forest without its `-lc-hr` companion | copy the companion from the same pool folder |
| `name clash with different bytes` | two builds with one file name (a kernel rebuilt at the same upstream version) | the old-kernel block in `official-part1.sh` |
| case e: `FAIL apt would install Debian's dpkg` | the pins of the tree under install are not in force, or the live set lost the edition's dpkg | `e1-sim-dpkg.txt` |
| case e: `REMOVED, not allowed: X` | the new tree makes apt remove X | `e2-sim-dist.txt`, the `Remv` line, and the `Conflicts`/`Breaks` of the new package that causes it |
| case e: `planted conffile edits were lost` | a maintainer script or the projection overwrote a person's edit | `e2-planted.tsv` lists path and package; read that package's postinst |

## Traps met while building this (symptom, cause, how it was found)

- **The pre-round check printed `FAIL` twice for one failure.** The second line came from the "FAIL line with exit 0" guard, which fired for logs of checks that had already failed. Found by reading the red run's `summary.txt`; the guard now looks only at checks whose exit status was 0.
- **`official-part1.sh` stopped silently after "base: N binaries, 0 source files".** With no source files in the forest, the glob `$SRC/source/*` stays literal, `readlink` fails inside `t=$(readlink ...)` and `set -e` ends the script with no message. Found by running the script on a small repository (the live one always has sources) and adding `set -x` to the failing section; fixed by skipping names that are not links and by creating the kernel list first.
- **A worktree's `.git` is a file pointing into the repository's common git directory.** Mounting only the worktree read-only into a container leaves `git` (used by `check_producers.py`) unable to work; mount `git rev-parse --git-common-dir` read-only at its own path too, and pass `safe.directory` through `GIT_CONFIG_*` variables.
- **Wrapper variables overwrite the script's.** A wrapper that exported `W=<its own folder>` for the script and then used `$W` for its own paths ran the wrong files; the script's `W` is the round folder, so wrappers use another name.
- **A tiny repository for a rehearsal still needs the lc1 companions.** publish-tree refuses a package with the lc1 mark when its `-lc-hr` documentation package is not in the source forest; copy both from the live pool (read only).
- **A shell command that matches its own command line.** `pkill -f mk-base.sh` run from a shell whose command text contained that name ended the shell (exit 144); kill by process id.
- **Disk.** The lean suite writes about 230 MB of scratch; a rehearsal on a small repository needs under 1 GB; the real round needs the floors in the house rules.

- **The proof's first checks failed on a good system: `dpkg --version` does not say the package version.** It prints `1.23.11+stereo3d2` for the package `1.23.11+stereo3d2+lc1`: the `+lc1` mark is the package's, not dpkg's. Found by reading `edition-dpkg.txt`, which holds both outputs side by side; the check strips the mark.
- **The same check then failed once and passed once on the same bytes.** Under `set -o pipefail`, `cmd | head -1 | grep -q x` fails when `grep -q` leaves early and `cmd` gets SIGPIPE. Found by comparing two runs whose recorded outputs were identical. Capture the output in a variable and match that.
- **The real upgrade died on its first package: "cannot execute ... required file not found" for `rm`, `tee`, `grep`.** A source of SparkyLinux's own `base-files` (a `/bin` directory, not the merged-`/usr` link) was a candidate in the container, so dist-upgrade replaced Debian's `base-files` and removed `/bin`. Found in `e2-dist-upgrade.log`: the first `Unpacking` line was `base-files`, and `e2-sim-dist.txt` showed its `Inst` line from `SparkyLinux:testing`. The edition's pins block that source for such packages; a rehearsal without the real pins must pin `origin repo.sparkylinux.org` at -1.
- **A rebuilt `+lc1` package cannot just get a new version in its control file.** The lc1 manifest (`usr/share/dpkg-stereo/lc/<package>/<arch>.json`) holds the version, and the control field `Sparky-Lean-Code: lc1 <sha256 of the manifest>` binds it; the gate says `lc identity or scope mismatch`. Change the version in the manifest, recompute the sha256, update the field and the manifest's line in `md5sums`.
- **`apt-get dist-upgrade` keeps a conflicting upgrade back instead of removing the installed package it conflicts with** (even with `Replaces` and `Provides`), so a planted removal shows as "kept back" in the proof, not as `Remv`; both are failures. The `Remv` check itself is exercised on planted logs by `test-checks.sh`.

## A package whose proofs bind another package's files (the saver catalogue gate, ORDER 146e)

gl-stereo-savers carries 132 receipts, each the SHA-256 of a saver executable and settings file of XScreenSaver and of gl-stereo's layer. They are true against one XScreenSaver build only: published 0.4.2 against the round's +stereo3d4+lc1 offered 1 of 132 savers and nothing said so.

- **Pin it:** the dependency on every package that owns a bound file is `(= version)`, generated at build time from the files the build just proved equal (`dpkg-query -S` then the installed version into a substvar; gl-stereo `savers/pin.py`), never typed and never `>=`. Both packages are ours and publish in the same round, so the pin costs nothing.
- **Gate it:** `official-part1.sh` runs `gl-stereo/packaging/check-round-savers.py --index $DEST` after publish-tree: it unpacks the tree's own packages in Python and refuses the round when the catalogue would offer fewer savers than it ships against that tree's XScreenSaver, or when Depends is not the exact pin. A round that rebuilds XScreenSaver without requalifying gl-stereo stops here with each saver, file and both hashes named. Exit 2 (no gl-stereo-savers, no xscreensaver, unreadable archive) refuses too: a gate that cannot look is not a pass.
- **Say it:** what a package cannot offer is named where the person looks (gl-stereo's saver list: "Not offered" and the reason), never dropped from a list.
- The same shape fits any package whose qualification binds files of another (check what its catalogue code does with a mismatch before trusting a `>=`).

## Rehearse before the real round

A dry round runs `official-part1.sh` with `ROUND_DRY=1`: the base need not equal the live tree (said loudly), the official key and `build.conf` are never read, and `ROUND_KEY_HOME`/`ROUND_KEY` name a throwaway key.
Make the base from a few packages of the live pool (their `-lc-hr` companions too) with `publish-tree.sh` and the throwaway key (`SPARKY_APPSTREAM=0 SPARKY_INSTALLABLE=off`), make the cohort one rebuilt package (the same package with a higher version), and run the round and the proof on them.
Plant the failures to see the stops: a commit that breaks a wired build script (the pre-round checks fail), a candidate that `Conflicts` with an installed package (case e: packages kept back), a candidate whose postinst overwrites a conffile (case e: planted edit lost). On 2026-11-06 the rehearsal's green case passed 9 checks in about 4 minutes and both planted cases failed with those messages. A rehearsal case needs `E_PACKAGES` small, `E_I386=0`, `PROOF_PIN_DIR` (pins for a repository that has no `sparky-stereo-apt`) and `RUN_PROOFS_MIN_MIB` lowered; say so in the report, because it is not the full proof.
