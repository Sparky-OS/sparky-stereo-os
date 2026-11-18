# A publication round: frozen tree, pre-round checks, upgrade proof, reading a failure

**For the maintainer who turns accepted packages into one signed repository state.**
The round's scripts take a build-repository commit, check it, build the new tree from the accepted packages, prove that an installed edition upgrades to it, and stop on the first failure.
Written on 2026-11-06 from the rehearsal described under "Rehearse before the real round"; the machinery is the round folder's `official-part1.sh`, `pre-round-checks.sh`, `round-worktree.sh` and `run-proofs.sh` with its `proof-scripts/`.

## Before a round: what the merged tree holds that no stage carries

Start with a fetched, clean build-repository commit and the current cohort stage list.
A merged recipe can be newer than every stage even when the publication gate is green: that gate checks the selected packages, not recipes that nobody selected.
Keep one reconciliation table with package or source, published version, newest selected stage and its path, recipe version and source line, the change a person gets, and the action needed.

1. Read the published `Packages` and `Sources` indexes, and every binary and descriptor in every stage the cohort names.
   Read a Python cohort list with `ast.parse` and `ast.literal_eval` of its `STAGES` assignment; importing the module can write the shared cohort files.
   Match the source through each binary's `Source` field, including an explicit source version, as Debian Policy 5.6.1 specifies; a recipe folder name is not necessarily its source name.
2. Inventory the tracked producers, then read their version expressions without running them:

   ```sh
   git fetch origin +refs/heads/main:refs/remotes/origin/main
   git status --porcelain
   git ls-files sparky-os/packages sparky-os/upstream > recipe-files.txt
   rg -n 'VERSION=|NEW_VERSION=|NEXT=|--next |--newversion|edition_version' \
       sparky-os/packages sparky-os/upstream
   ```

   Check `CHANGELOG`, `debian/changelog`, version environment files, JSON suite manifests and the folders the producers name too.
   Resolve a successor to its current source; an older producer retained in the tree is not the shipped recipe.
   Parameterized producers need a row for each version that must be kept, including a compiler used to seed its successor.
   Inspect missing or uninitialized source checkouts explicitly; an empty folder is not evidence that no recipe exists.
3. Compare versions with dpkg, not string ordering or a version guessed from a filename:

   ```sh
   dpkg-deb -f "$DEB" Package Source Version Architecture
   dpkg --compare-versions "$RECIPE_VERSION" gt "$PUBLISHED_VERSION"
   dpkg --compare-versions "$RECIPE_VERSION" gt "$NEWEST_STAGE_VERSION"
   find "$BUILD_SCRATCH" "$LANE_STORAGE" -maxdepth 5 -type f \
       \( -name 'PACKAGE_*.dsc' -o -name 'PACKAGE_*.deb' \) -print
   ```

   A missing published package or stage is written as absent, not version zero.
   Keep full epochs and Debian revisions; distinguish the pipeline's terminal `+lc1` packaging mark from a source recipe that has not added it yet.
   A stage elsewhere is an **unlisted stage**, not an unbuilt package.
   Verify its descriptor, exact binaries, source components, build record, checksums and acceptance before proposing it for the cohort.
   A descriptor alone, or an unsealed candidate of the same upstream version, is not a publication stage.
   Name unreadable directories and the depth bound; do not turn a bounded search into a claim about every disk.
4. Build missing small packages from the merged commit with their own recipes and provenance init.
   Give each recipe its own source date; unset an earlier recipe's `SOURCE_DATE_EPOCH` before the next init.
   Retain the complete source package and rebuild its binaries from that descriptor so `.buildinfo` and `.changes` describe the staged files.
   Compare payload, controls, permissions, ownership and links with the recipe output; describe archive timestamp differences separately.
   Require complete clean build records, Lean Code and HR checks, lintian compared with the published lines, the zram gate with its notes read, and the archive link gate where applicable.
   Supply unchanged edition dependencies on both the candidate and previous sides of that gate.
   Prove the exact upgrade with apt's `Inst` lines and the actual installed version; no removals alone does not prove an upgrade happened.
5. Hand back the stages, checksums and table, plus the larger builds and missing dependencies that remain.
   Keep the round's current frozen inputs read only; copy, never hard-link, a stage or published archive.
   Do not edit the coordinator's cohort list from a worker lane.

Trap found while preparing a round:

- **Symptom:** a package selected for a round was older than the accepted recipe, and other merged recipes had no selected stage at all.
- **Cause:** the cohort was assembled from known stage folders; nobody compared all current recipe versions against both the published indexes and every selected stage.
  An exact newer stage outside that list was missed too.
- **Fix:** build this table before freezing the round, locate unlisted stages with a bounded search, build the missing small packages, and name the large work explicitly.
- **How found:** the recipe's `VERSION` and changelog were read against the published control and the staged descriptor, then every listed stage was inventoried by binary/source identity.

The pre-round checks also run `python3 iso-build/tests/test-zram-check.py`, in the same isolated container form as the other checks.
Prove a new check twice on immutable copies: green on the merged tree, red after disabling one gate refusal deliberately.
The red summary must name the failed check, end with the round-stop message, and return 1.
A summary pipeline runs in a subshell; update the aggregate failure variable outside it, or a printed FAIL can still return success.

### A stage taken only in part

Inventory the binaries before choosing folders:

```sh
dpkg-deb -f PACKAGE.deb Package Source Version Architecture Sparky-Lean-Code
dpkg --compare-versions OLD_SOURCE_VERSION lt NEW_SOURCE_VERSION
```

Keep a take list and a leave-out list with each stage, exact relative filename, source, source version, binary name and architecture.
Choose one authoritative source generation, including its HR and debug companions, then keep its descriptor, checksum-bound source components, buildinfo, changes and build record together.
A parent stage can contain a superseded installer, hardware helper or compositor alongside packages still needed by the round.
An input retained for another recipe is not a second candidate to publish.
Never copy that parent wholesale into the cohort.
Where a selected binary has the same version and architecture as a published binary, compare their SHA-256 too: equal bytes need no replacement, and different bytes at one published identity stop selection.

Traps found by archive and source inspection in ORDER 587:

- **Symptom:** the advertised supersession list leaves older packages beside their successors.
  **Cause:** the review named the obvious shared library but missed another source in a partial stage.
  **Fix:** compare every binary's source identity and version, then emit exact leave-out filenames for all older generations, not just the sources named in the brief.
  **How found:** reading the controls exposed an older hardware helper, installer settings and compositor in otherwise useful stages; dpkg's version comparison selected their accepted successors.
- **Symptom:** a working staged program has no publishable Lean Code source.
  **Cause:** its application build is staged as one unqualified binary; the descriptor, HR companion and release build record were never made.
  **Fix:** record a successor-build gap and keep that binary out of the take list until the tree's source preparation and release gates finish.
  Do not infer qualification from a version suffix alone: inspect `Sparky-Lean-Code` and the source closure; some qualified packages have no `+lc1` in their version.
  **How found:** Kamoso's staged control had no mark and its stage had no matching descriptor, unlike the qualified Camera page beside it.
- **Symptom:** a large compiler or suite is reported unbuilt although exact accepted outputs exist.
  **Cause:** the known stage list omitted outputs under another scratch root; the recipe keeps its result under `out`.
  **Fix:** search for manifests and descriptors too, then check the binaries, source closure, clean complete records and acceptance before proposing the discovered output.
  Keep an older compiler needed as the build seed separately from its successor's publication set; duplicate binary names cannot both be authoritative.
  **How found:** the version environment files and suite manifest matched retained outputs whose SHA256SUMS and records verified.
- **Symptom:** checksums and the lc1 control mark pass, but the build record says `unrecorded: ["buildinfo"]`.
  **Cause:** the staged build has its source and binaries without the binary build's metadata.
  **Fix:** retain this as a qualification gap; rebuild the small package through its recipe and source-build route before selecting it.
  Never edit the old record to make it look complete.
  **How found:** reading every selected source's record found this in the look package; its stage had no `.buildinfo` or `.changes`.
- **Symptom:** a complete clean record names a descriptor hash different from the staged descriptor, although the stage's SHA256SUMS passes.
  **Cause:** the manifest and record certify different descriptor bytes; checking each file against only one of them misses the disagreement.
  **Fix:** compare every recorded binary and metadata hash with the actual staged file, and hold the affected source until its source and build evidence agree.
  **How found:** the graphics helper's record bound another `.dsc` hash in three successive stages; the source-component manifests themselves verified.

A source-closure take list is an exact set of paths, not just source/version pairs.
Cross-check the ancillary expansion against the successfully qualified artifacts and the copied pool manifest in both directions.
A shared orig tar may be referenced by both excluded and selected descriptors; a duplicate recipe build may have the same version with different receipts.
Only the exact qualified closure decides which of those paths is taken.

- **Symptom:** the expanded take list had the expected file count but selected three receipts of a discarded duplicate build and omitted a relocated record and two shared source components.
  **Cause:** ancillary ownership was inferred from source/version and the first descriptor encountered, without comparing the complete path sets.
  **Fix:** bind selection to the exact successfully qualified artifact manifest, retain all other paths with their leave-out reasons, and assert set equality with the copied pool, rather than comparing counts.
  **How found:** a two-way path-set comparison exposed three extras and three omissions despite equal totals; after correction all paths matched, with the discarded receipts still explicit in the leave-out list.

### Repair a receipt gap without choosing a different accepted binary

A missing or disagreeing build receipt is repaired by rebuilding the exact retained descriptor in the lane's own builder.
Compare every payload and control member, including modes, ownership and links, with the accepted archives before admitting genuine rebuilt receipts.
Keep both the initial failure and the member comparison.
A matching HR companion alone does not establish equality of the primary archive.
When a member differs, hold the source and its required companions; continue the remaining freeze if its dependencies permit, following the coordinator's cohort ruling.
Do not substitute the rebuilt binary or attach its receipts to the accepted archive without equality.
If the build record names another descriptor, search only the authorized bounded inputs and say which descriptor was actually rebuilt; an unavailable recorded descriptor leaves the original source identity unproved.

- **Symptom:** the replacement freeze stopped twice for receipt-only gaps, then a Graphics rebuild produced seven different payload/control members although its HR archive matched.
- **Cause:** the accepted cohort contained missing binary receipts and a descriptor hash disagreement; neither the manifest nor matching companion bytes certified the primary binary's relationship to the available descriptor.
- **Fix:** rebuild the retained descriptor, admit complete genuine receipts only after all-member equality, and hold a differing source with its required family. For this cohort the coordinator required Graphics and both Qt sources to travel together, so all three stayed out while the remaining cohort continued.
- **How found:** Calamares branding's two archives matched and its repaired receipts passed the source audit; Graphics' streamed payload/control maps exposed five differing installed files and two control members. The original recorded descriptor was absent from the bounded search, so its origin was not inferred.

### A clean successor when the accepted descriptor cannot reproduce its binary

An exact receipt repair and a new source-built successor are different operations.
When the available descriptor does not reproduce the accepted binary and the recorded descriptor is unavailable, keep that failed repair and obtain an explicit successor ruling.
Build the new version from the authorized recipe, retain its real source-build receipts, and compare the result with the accepted installed package.
Compare every member's path, type, mode, owner and link; restore script/data files through their verified HR blobs before comparing authored bytes.
For compiled files retain exported dynamic symbols, NEEDED entries and complete string-table dumps, with only the authorized version/build-identifier differences normalized.
Report compiler and Lean toolkit versions independently; projected bytes from different toolkit versions need not be identical when the authored bytes are.
Keep short binary-section fragments separately from actual strings, rather than silently removing them from the evidence.

- **Symptom:** the Graphics receipt repair changed installed files even though its HR companion matched; the recorded descriptor was no longer available.
- **Cause:** the retained descriptor was not sufficient evidence for the accepted compiled archive, and a later Lean renderer also changed projected script bytes.
- **Fix:** preserve the failed repair, build an explicitly authorized version-only successor with genuine receipts, then compare restored authored files and compiled interfaces against the accepted archive. Keep its exactly pinned Qt family together. Never weaken the all-member equality required for an ordinary receipt repair.
- **How found:** streamed member comparisons separated the source mismatch from projection differences; verified HR restoration matched authored files, while ELF exports, NEEDED libraries and string dumps established the successor comparison. Its actual source build and all 14 package tests were retained separately.

### Discovery depth and processor variants

State the directory-discovery bound separately from the depth used to inventory a discovered stage.
Inspect a brief's named subfolders explicitly, retaining the same read-only rules and recording unreadable paths.
A file search bounded from the storage root can omit an accepted generation inside `stage/superseded/SOURCE-VERSION/` even though it found the stage itself.
Record which files were inspected; directory discovery alone is not source-closure verification.

Read `Architecture-Variant` beside `Architecture` when inventorying processor-specific archives ([processor-level packages](cpu-level-packages.md)).
An archive named with `amd64v3` can still say `Architecture: amd64`; keep its variant in the identity used to compare it with published binaries.
A shared native architecture and version does not make a variant an in-place replacement for the baseline.
Neither its filename nor its control field establishes publication acceptance.

Traps found during bounded discovery in ORDER 701:

- **Symptom:** the requested hardware helper generation was missing from the initial file inventory, while newer held generations were present.
  **Cause:** the four-level file search from the build-storage root stopped above the accepted files inside the named superseded subfolder.
  **Fix:** keep directory discovery bounded, then inventory the discovered stages and explicitly named subfolders with a separately stated depth.
  **How found:** a direct read-only search of the brief's named superseded folder located the exact descriptor and both binary companions.
- **Symptom:** baseline and processor-specific binaries appeared to share the same package/version/native-architecture identity.
  **Cause:** the first inventory kept `Architecture` but omitted `Architecture-Variant`.
  **Fix:** retain both fields and keep variants outside the candidate set until their own acceptance is recorded.
  **How found:** controls of staged stereo-library variants said `Architecture: amd64` while their filenames named `amd64v3`; reading the additional control field distinguished them.

### Compare installed paths as well as archive listing lines

Keep the complete `dpkg-deb -c` diff, then map every removed line to the archive member it describes.
Normalize only the presentation of directory paths (`./usr/` and tar's `./usr` name the same directory); retain file names, modes, ownership, links, sizes and content hashes separately.
A timestamp change is a changed listing line, not a removed installed file.
Keep reviewed explanations keyed by binary and installed path beside the raw comparisons, and refuse an unreadable listing line.
For an HR blob, follow the old manifest to its installed file and verify the replacement blob against the successor manifest after decompression.
A content-addressed blob's name changing alone does not show loss of the authored file.

Traps found while qualifying a round:

- **Symptom:** the comparison reported thousands of unresolved directory listing lines although their contents remained.
  **Cause:** `dpkg-deb -c` prints trailing directory slashes that the tar member names can omit; the archive root may be `.` rather than an empty path.
  **Fix:** normalize those directory presentations before matching, keep all metadata changes visible, and test root, ordinary directory, symlink, hardlink, names containing spaces and malformed input separately.
  **How found:** the unresolved lines were compared with the independently streamed tar member map; rerunning against the same immutable inputs resolved the false entries without dropping a diff line.
- **Symptom:** fresh generated kernel metas would stay at the published version while the other task metas upgraded.
  **Cause:** their versions derive from the kernel recipe independently of the meta source version, and a version without the published terminal `+lc1` sorts below that published version.
  **Fix:** use the generator's supported kernel-meta suffix for the round, including the terminal mark, compare every generated binary version with dpkg, and retain the actual source-built generation. Do not repair the control files after building.
  **How found:** a per-binary generated-versus-published control table exposed the ordering before the pool froze; `dpkg --compare-versions` confirmed it and the regenerated versions sorted above every published kernel meta.

### A stage accepted after the proof froze

A passing transaction and link check qualify their recorded archive identities, not every package that later enters a stage folder.
If a stage is accepted during that check, follow the coordinator's written instruction: rerun against the extended pool unless that instruction explicitly permits a separate hand-off for the round.
With that permission, finish the frozen check, retain its pool hash, and supply a separate per-source reconciliation and exact add/leave-out filenames for the late stages.
Name both scopes in the report; the person publishing still qualifies and rehearses the extended pool.
A later successor replaces the old source family, including its companions and metadata; it is not added beside it.

Trap:

- **Symptom:** a green installed proof is cited for a cohort whose FFmpeg, player, stereo library or thumbnailer arrived after its inputs froze.
- **Cause:** the accepted stage list advanced while the test was running, but the report treated that list and the frozen archive pool as the same thing.
- **Fix:** retain the exact proved pool and, only with explicit permission, a separate late-stage add/leave-out list; otherwise repeat the proof with the new pool. Check each late descriptor, component hash, binary Source field and listed build-record hash in place. A descriptor stored in the source subfolder may be checksum-covered separately from an architecture's binary build record; state which record actually names it.
- **How found:** compare the frozen index hash and transaction targets with the late binaries' Source versions and the time of the coordinator's exception. Resolve relocated source metadata only inside that stage's known source folder and require the exact recorded hash.

### Reused source components keep the selected generation's identity

An upstream orig archive can be shared by an old held descriptor and its accepted successor.
The archive's basename and first inventory owner do not decide which source generation takes it.
When admitting an exact metadata-qualified path, copy its source name and source version from that qualified closure as well as its hash and size.
Audit the independently copied pool again so a stale table label cannot create a descriptorless source group.

Trap:

- **Symptom:** auditing the copied pool creates a source group without a descriptor, although every copied hash agrees.
- **Cause:** Plasma PA's reused orig archive and detached signature inherited the first descriptor's +stereo3d1 label while the qualified closure was +stereo3d2.
- **Fix:** the qualified closure's identity overrides the initial inventory owner; correct the two report rows without changing any archive or pool manifest.
- **How found:** a copied-pool metadata audit grouped those two paths separately; a fixture with held and accepted descriptors sharing one orig archive failed before the correction and passed after it.

### Resume an unchanged pool after a capacity ruling

A written increase in scratch allowance changes the resource envelope, not the frozen cohort.
Remove the incomplete roots and data no completed check needs before restarting the whole failed target scope.
Verify the pool manifest and every listed checksum, and keep annotations unchanged too when the ruling says no pool file changes.
Apply the new free-space floors to both the outer monitor and archive qualifier.
Retain sampled usage, maximum observed allocation, sampling interval and disk free-space values; a sampled maximum is not a continuous high-water mark.
Worker count can change within the measured paired-root budget while the validator files and target set stay unchanged.

Trap:

- **Symptom:** the installed proof and native archive checks pass, but the required meta source remains unqualified after a capacity stop.
- **Cause:** the previous allocation cannot hold the paired dependency roots, verified cache and stop margin together.
- **Fix:** obtain the coordinator's written resource ruling, clear incomplete scratch, verify the unchanged pool and rerun the complete failed scope with explicit limits and retained peak samples.
  Late accepted work still follows its own cohort ruling; a capacity increase does not admit it.
- **How found:** the old 9.6 GiB guard stopped with one complete top-meta root and an incomplete predecessor; Continuation4 authorized16 GiB and a12 GiB root free-space floor, so the same60 targets could be retried without regenerating packages or lists.

### Public indexes between bounded invocations

One copied pool can need separate complete native and meta invocations to stay inside its scratch allocation.
Each invocation still compares old and new against one frozen signed public snapshot.
Record every invocation's metadata hashes; do not infer that a later invocation read identical public indexes.
If an external index refreshed, retain the record diff and check every selected resolution identity on both sides.
A changed selected input needs fresh qualification under the intended snapshot; an unused index record is reported without pretending that its program was tested.

Trap:

- **Symptom:** native and meta qualification metadata name different public index hashes although the pool manifest did not change.
- **Cause:** Sparky's tiamat archive refreshed five upstream programs between two bounded invocations.
- **Fix:** require parent and private worker metadata to agree inside each invocation, retain both signed snapshots, diff the changed records and audit all selected identities against those changes.
  Keep the local pool identity and the external snapshot identities distinct in the hand-back.
- **How found:** comparing all 15 metadata entries located tiamat's InRelease and Packages changes; the record diff identified code, librewolf, meru, nuclear and opera-stable with unchanged relationship fields, then resolution package identities showed whether they entered any qualified root.

### A required package outside the accepted cohort

Resolve generated hard dependencies against the selected pool, published indexes and the edition's declared signed archives before freezing.
If only an unlisted stage provides a dependency, name it as such and check its source receipts; its presence is not publication acceptance.
Keep the designed dependency and obtain the coordinator's source-generation decision rather than deleting it to make APT pass.

- **Symptom:** a simulated dist-upgrade offered 111 upgrades and zero removals but kept the desktop meta back.
  **Cause:** the generated meta required the sound-defaults package, absent from the published tree and selected pool; the journal had accepted it but the take list omitted its stage, which also lacked binary buildinfo and changes.
  **Fix:** report the exact kept package and missing dependency, confirm its journal acceptance with the coordinator, qualify the retained source through a genuine rebuild, and repeat the combined proof on one extended pool. Never equate zero removals with a successful uplift.
  **How found:** an exact-version install simulation named the unsatisfied Depends; the bounded stage table located its archives, the receipt audit found `unrecorded: ["buildinfo"]` and no matching changes, and the coordinator supplied the missing journal acceptance.

### A verification monitor must be able to measure its scratch

Run archive qualification as the lane UID with an explicit writable HOME and private HTTPS APT configuration.
A scratch measurement that fails is a refusal, not a size of zero or permission to continue without the monitor.
Stop only the owned task named by that monitor and retain its diagnostic before retrying.

- **Symptom:** `du` reported permission denied on an archive context and the budget monitor exited while its child task still existed.
- **Cause:** a root verification invocation created a private mode-0700 directory that the lane UID could not inspect; the monitor did not handle a failed measurement.
- **Fix:** use the lane UID for the archive gate, repair ownership only inside the lane's scratch, and make measurement failure stop the literal named task. Exercise that refusal with an unreadable-measurement fixture.
- **How found:** the monitor's traceback and directory owner/mode identified the failure; its fixture then proved the exact stop command and refusal exit.

A live held stage can also change after initial discovery.
Retain disappeared paths as observations, inspect the newly seen descriptor/binaries within that named root, and report a newer unlisted generation without adding it to the frozen pool.
The pool's accepted copies and checksum identity stay independent of that live folder.

- **Symptom:** a whole-pool lintian scan had produced no verdict while its pre-extraction scratch passed 4 GiB beside active archive-link roots.
- **Cause:** submitting every binary together retained many extracted source groups before finishing the scan; compressed pool size did not predict its peak allocation.
- **Fix:** stop that incomplete invocation without counting it, then scan complete source families one at a time, keeping both architectures and companions together. Pair each family with every corresponding published binary, retain return codes and raw tags, and assert full current/published coverage before calculating the delta.
- **How found:** measured scratch separated lintian's growing extraction tree from link roots; the replacement driver emitted each completed family with its binary counts and diagnostics while staying inside the shared lane budget.

- **Symptom:** a real `init.d-script-missing-lsb-section` warning remained in the raw diagnostic list instead of the tag totals.
- **Cause:** the tag parser allowed letters and hyphens but not the dot in this valid tag name.
- **Fix:** retain raw output, parse dotted names too, and explicitly reclassify the previously retained line when rebuilding the delta; do not rescan or alter package archives for a reporting-only correction.
- **How found:** the final QEMU family had the same warning on both sides. Reparsing added exactly one tag to each total, preserved every raw log hash, and left the complete delta unchanged.

- **Symptom:** the 9 GiB guard stopped concurrent archive qualification and lintian below the brief's 10 GiB allocation, after hundreds of dependency cases had resolved.
- **Cause:** four paired Qt dependency roots, their verified archive cache and another check's extraction tree share one allocation; bounding each check independently does not bound their sum.
- **Fix:** retain the interrupted contexts as incomplete evidence, remove their unpacked roots, verify every reused cache object's content hash, and repeat the complete archive gate with fewer workers under the combined guard. Use one worker when one paired case approaches the allocation. Reuse only completed paired lintian families against the same sealed pool, validating coverage and retained raw diagnostics; an interrupted family is rerun. Never infer an archive pass from resolved cases alone.
- **How found:** the guard recorded exact scratch/free-space bytes and stopped only named owned containers; per-directory measurements identified the overlapping roots, and the bounded invocation uses fresh contexts with the unchanged frozen binary inputs.

Worker count and the CPU quota available inside one check are separate controls.
Two simultaneous large theme closures can still exceed the allocation; one Python worker leaves room for their paired roots.
The build repository's `tools/publication-reconcile/archive-one-worker.py` configures the toolkit's worker-count provider while native subprocesses retain the container's four-CPU quota.
Keep every validator file identical to the frozen tree and retain its hash comparison; test complete ordered item coverage, refusal propagation and the release command's return/exit status before using the adapter.
This configures scheduling only; a partial run is still incomplete and every selected package is checked again.

### A clean simulation can still select the old edition

The flat candidate index must carry the same Release Origin used by the edition's preferences.
Before the real transaction, require an exact-version Inst line for every installed package selected for replacement in the frozen pool.
Retain a target table derived from the audited controls and reject a check that exercises no installed replacement.

- **Symptom:** the simulation returned zero removals and nothing kept back, but offered only unrelated Debian updates while selected Qt and edition successors stayed old.
- **Cause:** a regenerated flat Release omitted Origin, so the edition's origin pin continued to prefer the published packages over the newer local candidates.
- **Fix:** restore the declared Origin/Label in the local index, seal the corrected index, and restart the actual proof from the untouched published baseline. Keep the invalid attempt separate and check exact selected versions before installing.
- **How found:** the Inst lines had none of the expected successors; the before snapshot still held published versions, and the Release metadata explained the preference mismatch. The corrected simulation offered 250 Inst and all 164 installed selected replacement targets; negative checker fixtures refuse missing or wrong-version Inst lines.

### A clean simulation does not run maintainer scripts

After a required package's configuration fails, preserve the complete transaction, installed statuses and `dpkg --audit` before changing anything.
A source needed by the edition metas cannot simply be removed from the cohort.
Do not turn that failed transaction into a pass by deleting its hook or silently replacing the configuration that triggered it.
Supply a focused reproducer and a proposed source fix separately; the successor and the combined transaction still need qualification.

- **Symptom:** a simulation offered 170 Inst, zero Remv and no kept packages; the real upgrade returned 100 and left the top edition and language meta unpacked.
- **Cause:** the new language task's postinst called its queue helper, which rejected the baseline's comment-only generated locale file because no `LANG=` assignment existed. The helper handled an absent file differently from an existing file without that assignment.
- **Fix:** hold the required transaction and report the exact dependency chain. Propose treating an unset assignment consistently with the existing absent-file rule while preserving rejection of unsupported explicit locales, then rebuild an accepted successor and repeat the frozen proof.
- **How found:** the real log named the postinst, baseline and failed-image locale bytes matched, the status readback showed the helper half configured and both required metas unpacked, and isolated function fixtures reproduced the refusal and exercised the proposed change.

### Keep the verification image's bootstrap explicit

A minimal no-Recommends bootstrap is not the full image package list.
Supply the tools its kernel hooks and language fixtures actually require and record that test scope.

- **Symptom:** the baseline package transaction and audit passed while its initramfs log reported a missing cpio and failed microcode prepend; a Lean fixture separately failed with a missing Go executable.
  **Cause:** the minimal builder omitted tools normally supplied by image/developer recommendations; the initramfs hook's diagnostic did not make the package transaction fail.
  **Fix:** install the bootstrap tools before using the baseline, regenerate its initramfs, and run the real compiler-backed fixtures in a declared verification image. Keep the initial logs and the repaired baseline readback; an empty audit cannot certify a boot image.
  **How found:** the complete install log named cpio, and the fixture traceback passed a missing executable to subprocess; adding the declared tools let those actual operations run.

When immutable offered inputs move to different paths, use a fresh archive invocation context.
A content-addressed local universe may retain symlinks and provenance to its original source paths even when the archive hashes are identical.
Reuse only the independently verified data cache, not that old universe metadata.
Reading the published tree read-only and letting the gate copy only selected archives avoids a redundant copy of the entire offered universe.
This does not permit changing or deleting an input while an invocation still uses it.

### Task metadata is generated after the cohort is known

A task producer's caller-supplied version is not a fixed newer release in its historical changelog.
Reconcile its generated relations separately from ordinary source versions.
In ORDER 587, source inspection located the desktop's Camera dependency in `lists/make-meta.py` and DisplayCAL's two role suggestions in `lists/suggests.tsv`.
Those are the inputs to the next meta build; this inspection alone proves neither a generated package nor an installed upgrade.
Compare every generated field with the published metas, explain each difference by its generating list or code line, then prove the transaction through apt's `Inst` lines, installed versions, no unexpected `Remv` and an empty audit.
For hardware-dependent software offered only on request, check it is absent after installing the tasks with the edition's normal recommendation policy.

Continuation lessons from ORDER 587:

- **Symptom:** `lc-successor.py` refuses a staged application with `not a +lc1 source`.
  **Cause:** a plain binary is not an earlier Lean Code source, and cannot supply that tool's retained toolkit or source-consumer plan.
  **Fix:** recover the exact Debian source, apply the already accepted application patch, then use `lean.debian_prepare` and the conventional source build to make its first lc1 source.
  Keep its complete build record and repeat the accepted behaviour test on the installed successor.
  **How found:** Kamoso's stage had only its plain binary, changes and patch; the successor tool's guard and the source-preparation route identified the correct first migration.
- **Symptom:** a standalone source rebuild produces different archive hashes although its installed contents are unchanged.
  **Cause:** archive timestamps and compression belong to the assembly, and can differ between direct assembly and `dpkg-buildpackage`.
  **Fix:** compare every payload and control member, including modes and links, then retain the actual source-built archives alongside the buildinfo and changes that name their hashes.
  Never attach metadata for one archive to another archive with equal payload but different bytes.
  **How found:** independent member maps and control comparisons showed identical look and HR contents; the source build's metadata identified which final archive bytes to keep.
- **Symptom:** `dpkg-genchanges` cannot find the generated `.buildinfo`.
  **Cause:** buildinfo was written directly into the final stage while genchanges still looked beside its binary inputs.
  **Fix:** keep source, binaries and buildinfo in dpkg's output directory until changes is generated; retain all final files, then write the build record once.
  `dpkg-genbuildinfo` uses `--build=binary`; do not assume every dpkg helper accepts `-b`.
  **How found:** the graphics recipe's failing path named the expected parent directory; the conventional source build showed the working order.
- **Symptom:** the meta link gate cannot resolve `sparky-aptus-appcenter`, and generation omits programs known by another archive.
  **Cause:** the qualification and generator catalogues contained Debian, deb-multimedia and the edition, but omitted the underlying SparkyLinux archives.
  **Fix:** mirror the edition's declared archives with their verified public keys before generating tasks or resolving their closures.
  Inspect the first policy attempt when the last attempt merely reports two mutually exclusive driver locks.
  **How found:** policy attempt zero traced the desktop through the memory page and Stereo AppCenter to the missing SparkyLinux package; its candidate appeared after the signed archive was added.
  Compare all generated relations with the published controls; unavailable names already absent from the published controls are distinct from removed functionality.
- **Symptom:** a full meta closure reports `symlink conflicts at ./etc/grub.d/10_linux`, although the boot package declares a literal diversion.
  **Cause:** its preinst creates the destination parent with `mkdir -p` between two diversion commands, outside the extractor's recognized command grammar.
  **Fix:** model only exact literal destination parents before use, with real dpkg-divert oracle tests and negative cases for unrelated directories, unsafe paths and shell operations; retain the collision refusal for every unmodeled script.
  Carry the corrected toolkit in its next package and repeat qualification against the complete cohort; never use an older boot sibling to make the check green.
  **How found:** the retained unmodeled-preinst report and the failing archive hash identified the accepted boot package; the oracle failed before the change and the 98 diversion tests passed after it.
- **Symptom:** the installed-state check says DisplayCAL is installed although no transaction installed it.
  **Cause:** a substring match for `installed` also matches dpkg-query's `not-installed` state.
  **Fix:** match the complete status value and retain the failed checker run; require the corrected overall rehearsal to exit zero.
  **How found:** the stopped container's status data contained no DisplayCAL installation while the checker used an unanchored grep.
- **Symptom:** a link qualification stops with `Invalid cross-device link` when adding a verified archive to its SHA-256 cache.
  **Cause:** moving only the cache to another filesystem leaves its temporary downloads on the original one; the final rename cannot cross filesystems.
  **Fix:** keep temporary downloads and the cache directory on one filesystem. Stop the run before relocating the scratch tree, verify the copied archive hashes, and restart the complete check; keep final publication stages free of caches.
  **How found:** the failing source and destination paths matched `download.part` and the relocated cache; `lean/archive.py` uses `temporary.rename(archive)` after checking the signed size and hash.
- **Symptom:** a task meta's installed upgrade passes, but its archive link gate reaches the scratch allocation before its predecessor closure is unpacked.
  **Cause:** the gate needs both complete dependency roots at once, besides the archive cache and diagnostics; the size of the meta archive does not predict that space.
  **Fix:** budget both roots and the cache inside the brief's allocation. If they do not fit, retain the diagnostics and nonzero exit, stop the gate, and hold the unqualified source group out of the take list while finishing the other requested proofs.
  **How found:** per-case disk measurements showed the completed current root beside the growing predecessor; moving verified cache files freed space but did not complete the paired-root check. The independently passing installed transaction remained a separate proof.
  A fresh-cache targeted retry distinguishes accumulated cache from a pair that cannot finish with the required stop margin.
  Record the complete root, incomplete predecessor, verified cache, sampled allocation and allocation after the stop; an incomplete predecessor does not establish an exact minimum.
  If that unqualified source supplies the required edition metas, hand back blocked with the unchanged pool identity; the passing installed transaction does not replace archive qualification.


## The recipe

1. **Freeze the build tree.** `round-worktree.sh WORKTREE [COMMIT]` makes (or reuses) a git worktree of the build repository at one commit; the default commit is `origin/main` as fetched now.
   Freeze the published archive inputs with verified independent read copies as well. A live archive can retain its SHA-256 while inode metadata changes, causing `supplied input changed after its universe was frozen`; keep that guard unchanged and follow [the frozen-input lesson](../../lean-code/references/lessons-2026-11.md). Check every copied hash and that source and destination have different device/inode identities; a symlink or hard link does not freeze the input.

   Every build-repository path of the round (`publish-tree.sh`, the lean toolkit, the supply-chain tools, the pre-round checks) points into that worktree, never into the shared checkout, because branches are merged into the shared checkout while a round runs for hours.
   It prints `round-commit <40 hex> <path>`; the round log, `round-commit.txt` and the supply-chain file `round-toolkit-ROUND.json` (listed in `SHA256SUMS`, so the detached signature covers it) name that commit.
   An existing worktree is reused only at exactly that commit and with nothing changed; any other state stops with the reason.
   Remove it when the round is published: `git worktree remove --force WORKTREE`.
2. **Pass the pre-round checks.** `pre-round-checks.sh WORKTREE OUTDIR` runs, each in its own container (image `lc-linebreak-rebuilds-311-test:1`, `--ulimit core=0`, `--network none`, the three `--security-opt` options `seccomp=unconfined apparmor=unconfined systempaths=unconfined` that the link-gate tests need for bubblewrap), the whole lean suite (`python3 -m pytest lean/tests`: 461 passed, 30 skipped on 2026-11-06, 4 to 5 minutes), `tests/reproducible-sources/test.sh` `tests/supply-chain/test-wiring.sh` and `iso-build/tests/test-zram-check.py`.
   It runs all four even after a failure, prints one PASS or FAIL line each, and exits 1 if any did not pass; `official-part1.sh` stops there, before it copies anything.
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
   Keep captured installed symlink targets as plain byte records, with their type recorded in the comparison table: absolute installed links can escape a source root and `dpkg-source -x` correctly refuses them.
   Extract every final `.dsc` with ordinary `dpkg-source -x` and repeat the file and link-target comparisons on that extracted source.
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
| `PRE-ROUND CHECKS FAILED` | one of the four checks | `OUTDIR/summary.txt` names it, `OUTDIR/<check>.log` has the output; the lean suite's first `FAILED` line names the test |
| `wiring: ... docker run lacks "${SPARKY_PROV_ARGS[@]}"` | a build driver does not pass the host's provenance facts | the file named on that line |
| `BASE is not live` | the base copy's InRelease hash differs from the server's | someone published since the copy; start from the live tree |
| `supplied input changed after its universe was frozen` | something touched a file of the base or destination pool while the link gate ran (a hard-link copy, a delete); the gate stamps inode, size and change times | never `cp -al`, delete or rename any tree sharing the pool during a run; reads are safe |
| `zram/zswap gate: refused, N finding(s) and M unreadable in ...` | a selected package sets zram or zswap up, pulls a zram package in, keeps the person from one, or carries a zram unit the gate cannot read | each finding names the package, the file and the line; [the zram and zswap gate](#the-zram-and-zswap-gate-its-verdict-and-what-to-do-on-a-refusal) below |
| `lc1: release blocked: (...): matching HR documentation package is missing` | a package with the lc1 mark went into the source forest without its `-lc-hr` companion | copy the companion from the same pool folder |
| `name clash with different bytes` | two builds with one file name (a kernel rebuilt at the same upstream version) | the old-kernel block in `official-part1.sh` |
| case e: `FAIL apt would install Debian's dpkg` | the pins of the tree under install are not in force, or the live set lost the edition's dpkg | `e1-sim-dpkg.txt` |
| case e: `REMOVED, not allowed: X` | the new tree makes apt remove X | `e2-sim-dist.txt`, the `Remv` line, and the `Conflicts`/`Breaks` of the new package that causes it |
| case e: `planted conffile edits were lost` | a maintainer script or the projection overwrote a person's edit | `e2-planted.tsv` lists path and package; read that package's postinst |

## The zram and zswap gate: its verdict, and what to do on a refusal

`publish-tree.sh` runs `iso-build/zram-check.py --debs-file` on every selected binary package right after the lc1 check, before the link gate and before anything is copied or signed.
The edition never sets zram or zswap up and never caps the person's choice of it; the rules, form by form with their sources, and how to write a unit that retires zram so the gate can read it, are in [power-idle, the zram gate](../../power-idle/references/zram-gate.md).

What the round's log shows:

```
zram/zswap gate: passed, nothing of zram or zswap of ours in N package(s), 0 refused (K -dbgsym and -lc-hr companions are checked through their packages) (the person's opt-in from Stereo APTus is allowed).
zram/zswap gate: K tear-down(s) let through, each read to its end. A tear-down stops, resets or removes zram, or reports; it sets nothing up:
  note: PACKAGE.deb: /usr/libexec/.../script:107: ... echo 1 >/sys/block/zram0/reset ... (a zram device reset, its memory freed: a tear-down)
  note: PACKAGE.deb: /usr/lib/systemd/system/NAME.service: a zram unit that only stops, resets, removes or reports: runs /usr/libexec/.../script, read to the end; 3 tear-down line(s) in what it runs, no set-up
```

A `note:` line is the record of what was let through and why; a round is not held by notes.
Read them once per round all the same: a note for a package that has no reason to touch zram is a question for its lane.
On the published tree of 2026-11-07 (902 packages checked, 66 seconds on four threads) the gate prints six notes: one for the Stereo APTus action's `systemctl stop`, five for the kernel settings' retiring lines and drop-ins.

```
zram/zswap gate: refused, 5 finding(s) and 0 unreadable in 1 package(s), 1 refused (...):
  PACKAGE.deb: /path:LINE: the line (what it is)
```

On a refusal:

1. **Leave the package out of the round and go on**, or stop the round; never pass a flag, edit the selection by hand around the gate, or change the gate inside the round's frozen worktree.
2. **Read the finding against the file** (`dpkg-deb --fsys-tarfile PACKAGE.deb | tar -xO ./path`): what does that line do when it runs, and can it make or grow a zram device or turn zswap on?
3. **If it can, the package changes:** remove the set-up, rebuild at a new version, stage it again.
4. **If it cannot** (the line only stops, resets, removes or reports) and the gate still refuses it, the gate is not exact for that form. That is a change to the gate in the build repository, tests first: a test that the form passes with its note, and tests that every set-up form is still refused beside it, in a unit and in the script the unit runs. A gate is never loosened to let one package through.
5. **`cannot be read` and `nothing passes unread` are refusals on purpose:** a unit whose program the package does not ship, a compiled program, text made at run time, a zram device used in a way the gate does not know. Make the unit readable ([how](../../power-idle/references/zram-gate.md#a-retiring-unit-the-gate-can-read)).

To see the step on its own, run the frozen worktree's `publish-tree.sh` on a throwaway tree: a source folder with the package and its `-lc-hr` companion, a destination that already holds the same files under `pool/main/<letter>/<source>/` (so the link and start gate has nothing new to qualify), a throwaway key, `SPARKY_APPSTREAM=0 SPARKY_INSTALLABLE=off`, in a container without network.
A fixture package that must be refused has to reach the step first: seal it with the tree's own `python3 -m lean.standalone TREE OUT --authoring DIR`, or the lc1 check stops the run before the zram gate looks.

Trap, found in ORDER 558:

- **Symptom:** the round refused the edition's own kernel settings package, accepted and proved on hardware a week earlier, with five findings: three units and a link `a zram unit`, and one script line `a zram device set up through sysfs`. The published version of the same package, with the same script and two drop-ins for the same foreign zram units, had always passed.
- **Cause:** the gate judged a unit by `zram` in its file name, so new units named after what they retire were refused and older drop-ins with neutral names in a zram folder were never read; and its sysfs rule took a line that reads `disksize` and writes `1` to `reset` for a write to `disksize`, because the write was looked for anywhere on the line.
- **Fix:** the gate reads what a zram unit does (its `Exec` lines and the script they run, to the end) and where each write goes; a tear-down passes with a note, every set-up form stays refused, and what cannot be read is refused.
- **How found:** the five findings were read one by one against the unpacked package (what runs, what it can do to a device), then the gate was run on the published version to see why it had passed: its file list showed the two drop-ins the name rule never matched.
  Before accepting the changed gate it was run, old and new, over every package of the published tree: the same verdict for every package, six notes more.

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

## A round that stops moving: one package, one processor at 100 % (ORDER 622, round r1116a)

- **Symptom:** Part 1's log ended at `== publish-tree` for more than four hours; one `python3 .../zram-check.py --debs-file ...` at 97 % of a processor, its `dpkg-deb --fsys-tarfile` child asleep for almost as long.
- **How the cause was found:** the child's command line names the package (`pgrep -P PID -a`), and its line number in the round's `zram-debs.txt` says how far the gate is (634 of 1,598, unchanged between two looks). The gate was then run on that one package with a stack dump on a timer (`faulthandler.dump_traceback_later(90, exit=True)` before `runpy.run_path(...)`), which named the line.
- **Cause:** a pattern of the form `[^separators]+\.md\b` read with `findall()` over a compiled file. In a long run of bytes with no separator every start position scans to the end of the run and back: quadratic. NVIDIA's `libnvidia-present.so` (66 MB) has such runs.
- **Fix:** find the endings first (`\.(?:md|markdown)\b`, linear), then each ending's run of path bytes. The new function was compared with the old pattern on 200,000 generated byte strings and 700 real files before it replaced it, and the package is read in under four seconds.
- **Restarting the round:** stop Part 1 by process id (its log gets `part1 exit 143`), keep its logs, remove the frozen worktree, `src`, `dest`, `tmp`, `lc-scratch`, the scratch folder and the non-empty `pre-round` folder (Part 1 refuses each), and start again with `ROUND_COMMIT` naming the round's first commit plus only the fix, on a branch pushed under the fix's number. The cohort stays the same.
- **Rule for a gate that reads compiled files:** no pattern that can backtrack over a run of arbitrary bytes; test it on the largest library of the archive, not only on fixtures. When a round's step is quiet for longer than its last run took, look at the process before waiting further.
