# A publication round: frozen tree, pre-round checks, upgrade proof, reading a failure

A core limit of exactly 1 suppresses the piped core helper; a zero limit does not, as the [crash trap](../../stereo-proof-rig/SKILL.md#traps-that-fooled-us) explains.

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

### Compare generated kernel-meta versions with the published controls

A round suffix is a Debian version input, not merely a unique label.
Before staging generated metas, read each published kernel-meta Version and require `dpkg --compare-versions "$new" gt "$published"` for a replacement.
Perform that comparison for every generated binary, including kernel metas whose version is independent of the ordinary round version.
After generation, repeat it on `dpkg-deb -f "$deb" Version`, and retain the installed-target check in the upgrade proof.

- **Symptom:** apt's simulation offers many upgrades, no removals and nothing kept back, but does not offer two selected kernel metas.
- **Cause:** a generated `7.3.4+stereo3d18+round20261121.794` sorts below published `7.3.4+stereo3d18.703+lc1`; the added plus suffix is less than the existing dot suffix in Debian version ordering.
  The round preparer supplied that suffix without comparing the resulting version to the published control.
- **Fix:** reject that generated version before freezing and generate a monotonic version through the recipe's supported input; an already frozen failing pool stays blocked, with its target mismatch preserved.
  The correction still needs source receipts, qualification and the actual installed upgrade proof.
- **How found:** ORDER 794's installed-target assertion compared 61 selected upgrades against the full apt Inst log and named both missing metas, despite a simulation with 78 Inst and zero Remv.
  No real upgrade had run when the check stopped.

### Check the whole output set before repairing receipts

Before comparing members, compare the exact binary filename sets from the accepted descriptor, existing receipts and retained stage with the rebuild's outputs.
Require every primary, debug and HR archive named by the source to have an accepted reference.
An equality check over only the files found in both folders cannot certify a missing companion.
Keep the set comparison beside the member comparison and the repaired receipts.

- **Symptom:** a receipt repair appears possible because the main binary and descriptor are present, but an existing receipt names a debug archive absent from the stage.
- **Cause:** comparing only retained files would leave part of the source build without an accepted reference.
- **Fix:** hold that source when the missing reference cannot be recovered within its authorized stage; do not manufacture an accepted debug archive from the rebuild.
  For complete sources, require equal output sets before checking every payload and control member.
- **How found:** the receipt filenames exposed two incomplete source families during ORDER 794; eleven other repairs passed both exact output-set equality and all-member comparison.

### Carry a held generation through dependency selection

A newer accepted binary without its own source closure remains held under the coordinator's ruling.
Select the newest earlier accepted generation whose complete closure is available; if it is already published, retain the published bytes.
Read every candidate's actual dependency constraint against that version before freezing the pool.
Hold any dependent source whose version requirement cannot be met, and stop the round when a required meta cannot survive that hold.

- **Symptom:** retaining an earlier complete library appears to solve a binary-only stage, but a separately staged integration pack still cannot install.
- **Cause:** the pack requires the held library's newer version explicitly; acceptance of the pack does not relax that constraint.
- **Fix:** keep both the newer library and that pack out, name the retained published version and each unsatisfied relation, and qualify the remaining metas against the actual supplied universe.
- **How found:** ORDER 794's source inventory found no complete intermediate layer, and reading the integration pack's Depends exposed its minimum version; the required edition meta passed its archive check with the earlier published layer retained.

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

### Check source closure before copying an accepted binary cohort

An accepted application test and a complete binary `SHA256SUMS` do not establish that its source archives and receipts survived cleanup.
Before the large copy, group the accepted binaries by their control `Source` and source version, then require a matching descriptor and its named components for every group.
Search the explicitly named outputs as well as bounded discovered stages; a result directory need not be named `stage` or `out`.
Keep missing paths and unreadable directories in the search evidence, and distinguish "absent from the allowed search" from "absent everywhere".
A receipt-only repair requires the retained descriptor and binaries; it cannot manufacture a missing descriptor or certify regenerated source archives.
Report that source gap and keep the affected generation out until its source recovery or successor build is authorized and qualified.

Traps found in ORDER 794:

- **Symptom:** a fully accepted multimedia cohort has 101 checksum-correct binaries but no matching source descriptor or build receipt for any of its six source generations in the allowed search.
  **Cause:** the retained stage contains only binaries, its checksum manifest and its retention note; neither acceptance nor binary checksum verification checks source retention.
  **Fix:** perform the per-source completeness check before freezing a pool, report the exact missing generations, and stop their selection without substituting an older descriptor or inventing receipts.
  Recovery was not performed in this preparation; a search outside the authorized scope or reconstruction needs its own instruction.
  **How found:** binary controls identified the six source/version pairs; a bounded metadata search and an independent stage-directory listing found no matching descriptors, buildinfo, changes or build records.
- **Symptom:** a no-follow directory walk still reads an archive through a symlink, or a missing explicitly named output silently disappears from the inventory.
  **Cause:** `os.walk(..., followlinks=False)` only prevents recursion into linked directories; file opens and a linked root can still follow links.
  **Fix:** reject symlink files and directories, check each explicit root's ancestors, record skipped links and missing directories, and retain separate directory-discovery and stage-file depth bounds.
  **How found:** inspection of the inventory's file-open path exposed the gap; temporary-directory fixtures cover a linked file, linked directory, linked root ancestor, missing root, depth limit and explicitly named output.

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

#### Qualify the pool after late acceptances

1. Verify the late stage's SHA256SUMS, then cross-check its descriptor, source components, .buildinfo, .changes and build record. Compare the source version with both the published and prepared versions using dpkg. Compare binary names, architectures, exact dependency relations and installed members against the generation the stage would displace. Record the function of every removed member. An unchanged orig archive can serve the replacement once its hash agrees with both descriptors.
2. Regenerate the metas from the merged build commit and the revised package catalog. Compare each meta's payload members and control relations with the prepared binary. Account for changes to Depends, Recommends and architecture coverage as well as version and receipt changes.
3. Update the take list, leave-out list and manifest from the same selection. Retain each displaced archive with its checksum. Regenerate the pool sums, APT indexes and candidate tree. Run `make-only-ours.py` on the resulting candidate and compare its outputs with the files in the selected APT policy package. A difference requires a qualified policy successor and another index refresh.
4. Verify installability against live Debian. If the scan is focused, record the changed package identities and their reverse-dependency coverage. Attribute residual failures on the same signed archive inputs. Run case e from the recorded published base, check the exact Inst versions and zero kept back, and measure each Remv. Bind both checks to the final pool hash.

Trap:

- **Symptom:** a later acceptance passes its receipt checks but makes an accepted settings page uninstallable when selected for the prepared pool.
- **Cause:** the fix was built on the published branch. The prepared pool already held a newer version of the same source with a different feature and an exact-version companion. The settings page required the prepared generation and explicitly broke older companions.
- **Fix:** qualify a source successor containing both accepted changes before selecting it. Compare the settings page's dependency and the old and new installed paths, then repeat the checks on the combined candidate.
- **How found:** dpkg version comparison and binary control fields exposed the impossible dependency. The payload comparison showed the older package removed the new feature's helper and took back the launcher the settings page now owned. The newer package's launcher still lacked the late fix.

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
By default, each invocation compares old and new against one frozen signed public snapshot.
The checked archive-transition exception described below may qualify a predecessor in a dated or mixed view; it never changes the candidate view.
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

### Case e's checks on a small rig, offline, before the round

To prove a few staged packages together without the full meta (a full case e needs about 28 GiB on Docker's disk), run case e's own checks on a smaller rig (rows 629/802, 2026-11-22):

1. A rig of the published tree installed as case e installs it: the edition's dpkg and dpkg-stereo first, then the packages under test and the packages whose files they touch.
2. Bring it up to date once with its own lists (`apt-get dist-upgrade`, no `update`), as a person's edition is after its updates and as a round's base is; download every installed package's .deb at its installed version into a folder (`apt-get download NAME:ARCH=VERSION`); commit that container as the rig.
3. The stages as one flat source whose Release says `Origin: Sparky Stereo OS`, so the edition's pin treats them as the edition's; read again only that source (`-o Dir::Etc::SourceList=FILE -o Dir::Etc::SourceParts=- -o APT::Get::List-Cleanup=0`).
4. One fresh container per mode, `--network none`: source `proof-common.sh` and `proof-checks.sh` read-only and call their checks (`check_inst_remv`, `check_real_log`, `plant_conffiles`, `check_planted_conffiles`, `check_verify`); require an exact-version `Inst` line for each staged package and none for anything else; put the folder of .debs into APT's cache only around `--verify --deep`, and take it out before the upgrade.

Traps:

- **Symptom:** the simulation installs a dozen Debian packages besides the stages. **Cause:** the rig was made by installing, so packages of the base image stay older than the rig's own lists. **Fix:** step 2. **How found:** the origins on the `Inst` lines.
- **Symptom:** `--verify --deep` prints thousands of `NODEB` rows and "This check is not complete". **Cause:** it compares each file with its package's .deb, taken from APT's cache first, else downloaded; offline, or for a version the lists no longer offer, nothing comes. **Fix:** the folder of .debs in APT's cache around the deep run. **How found:** its summary line.
- **Symptom:** a planted edit of an owning package's copy reads as lost, although it is there. **Cause:** while a diversion stays, the owning package's copy is at the diverted name; the check read the path. **Fix:** read the diverted name while the diversion stays, the path once it is gone.
- **Symptom:** case e passes while a lean conffile has no dpkg-stereo record, so a later change of that file by its package will be taken for the person's. **Cause:** `check_verify` reads `--verify`'s rows, and a lean file without a record gives none. **Fix:** dpkg-stereo 0.1.45 judges every such file (its record back when it is its package's projection, otherwise named as the person's), and a small rig adds its own check after the upgrade: `count-lost-records.py --list` must say 0. **How found:** `count-lost-records.py --list` before and after the upgrade (lean-code, [a file under a dpkg diversion](../../lean-code/references/diverted-files.md)).
- **Symptom:** a person's edit of `/etc/issue`, `/etc/zsh/zshrc` or `/etc/nanorc` on the published edition is replaced at the console's upgrade, and case e passes. **Cause:** `plant_conffiles` plants only into a package's `Conffiles`, and sparky-stereo-console ships these files at the diverted paths as plain files, which dpkg writes at every unpack. **How found:** edits planted in those files beside case e's own.

## The recipe

1. **Freeze the build tree.** `round-worktree.sh WORKTREE [COMMIT]` makes (or reuses) a git worktree of the build repository at one commit; the default commit is `origin/main` as fetched now.
   Freeze the published archive inputs with verified independent read copies as well. A live archive can retain its SHA-256 while inode metadata changes, causing `supplied input changed after its universe was frozen`; keep that guard unchanged and follow [the frozen-input lesson](../../lean-code/references/lessons-2026-11.md). Check every copied hash and that source and destination have different device/inode identities; a symlink or hard link does not freeze the input.

   Every build-repository path of the round (`publish-tree.sh`, the lean toolkit, the supply-chain tools, the pre-round checks) points into that worktree, never into the shared checkout, because branches are merged into the shared checkout while a round runs for hours.
   It prints `round-commit <40 hex> <path>`; the round log, `round-commit.txt` and the supply-chain file `round-toolkit-ROUND.json` (listed in `SHA256SUMS`, so the detached signature covers it) name that commit.
   An existing worktree is reused only at exactly that commit and with nothing changed; any other state stops with the reason.
   Remove it when the round is published: `git worktree remove --force WORKTREE`.
2. **Pass the pre-round checks.** `pre-round-checks.sh WORKTREE OUTDIR` runs, each in its own container (image `lc-linebreak-rebuilds-311-test:1`, `--ulimit core=1`, `--network none`, the three `--security-opt` options `seccomp=unconfined apparmor=unconfined systempaths=unconfined` that the link-gate tests need for bubblewrap), the whole lean suite (`python3 -m pytest lean/tests`: 461 passed, 30 skipped on 2026-11-06, 4 to 5 minutes), `tests/reproducible-sources/test.sh` `tests/supply-chain/test-wiring.sh` and `iso-build/tests/test-zram-check.py`.
   It runs all four even after a failure, prints one PASS or FAIL line each, and exits 1 if any did not pass; `official-part1.sh` stops there, before it copies anything.
3. **Build the tree** (`official-part1.sh`: base check, source forest, destination with the pool hard-linked from the base, `publish-tree.sh`, supply chain). Nothing is signed with a key the script was not given, and nothing is sent.
4. **Prove the upgrade on the edition's own dpkg.** `run-proofs.sh ROUND BASE DEST "a b e"`; case `e` installs the live set's `dpkg` and `dpkg-stereo` first, shows `dpkg --version` and `dpkg-query -W dpkg`, installs the package set under that dpkg, then runs `apt-get dist-upgrade` to the new tree and judges it on apt's own `Inst` and `Remv` lines (below).
   A stock-dpkg proof can pass where the edition's dpkg refuses (a shared Multi-Arch file that dpkg-stereo projected, ORDER 363).
5. **Attribute every newly installed package before the verdict.** apt 3's default solver prints `Inst` lines without a reason; its classic solver prints one per package: `apt-get -s --solver internal -o Debug::pkgDepCache::AutoInstall=1 dist-upgrade` on the committed case e base, with the pool as a second source. Every package must trace to a package the round takes on purpose; a chain through a package the round does not change is a finding ([below](#attribute-the-newly-installed-packages-with-apts-classic-solver)).

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

## Pre-freeze version coverage and a diverted file after the real upgrade

- **Symptom:** the version gate finds fewer replacements than the package inventory, even though generated kernel metas pass.
- **Cause:** reading only native and foreign-machine architecture indexes omits packages published in a separate `binary-all` index.
- **Fix:** give `tools/publication-reconcile/check-replacement-versions.py` every published Packages index, including `binary-all`, and the exact selected binary paths before freezing.
  Require every replacement to satisfy `dpkg --compare-versions NEW gt PUBLISHED`; retain named failures and refuse equal versions too.
  Generate kernel suffixes through the existing recipe input: replacing a published `.703+lc1` with `.794+lc1` keeps the generator's form, while ordinary metas keep their independent round version.
- **How found:** reading all four published indexes increased the non-meta replacement count from 142 to 185; the final generated-and-taken set contained 244 replacements and every comparison passed before copying.

- **Symptom:** an installed upgrade succeeds, preserves planted conffiles, has no removals and an empty dpkg audit, but `dpkg-stereo --verify` reports `CHANGED /etc/grub.d/10_linux`.
- **Cause:** a successor boot package diverts Debian's conffile and installs its own wrapper link at the old name; an earlier projection record still associates that name with Debian's hash.
  The package must not divert a conffile; teaching the verifier about diversions alone does not make that packaging valid.
  The verifier opens the old name and follows the replacement link rather than checking the diverted original.
- **Fix:** stop the proof and preserve its state; do not declare the change a planted person edit or loosen the proof's refusal.
  Hold the diverting boot generation and retain the published predecessor.
  Its owning package needs a successor that provides the boot menu without diverting the conffile; the verifier separately needs diversion-aware ownership checks and regressions for both preserved and changed diverted originals.
  That package repair is separate from a frozen round when the preparation brief forbids changing package content.
- **How found:** the diverted Debian file's SHA-256 exactly matched the stored lean hash, while the old name resolved to the new boot wrapper.
  Reading the verifier showed its direct open of the recorded path; the transaction and all installed selected versions had already passed.
  Inspect the retained baseline too: a pre-existing verification problem is a distinct fact, not an excuse to waive a new failure.

A rebuilt source reconstructed from Git does not qualify an existing binary merely because its complete output filename set matches.
Where the coordinator explicitly authorizes trying this despite a missing staged descriptor, bind both the recipe and upstream commits to the acceptance record and compare every member of every accepted archive.
A 20-for-20 output set with 90 differing payload/control members still fails receipt repair; preserve the comparison and hold the source and dependent pack.
This exceptional authorization does not change the normal requirement to rebuild the retained staged descriptor.

## Propagate holds and bind the evidence of a replacement preparation

- **Symptom:** removing a held generation leaves a selected companion or generated meta requiring it.
- **Cause:** source qualification and acceptance were checked independently of the taken packages' dependency and joint-acceptance conditions.
- **Fix:** read every taken Depends, Pre-Depends and Breaks and the relevant acceptance records before regenerating metas. Hold required or inseparable companions; keep independently accepted successors when the published predecessor satisfies them. Record the relation and acceptance evidence for each decision.
- **How found:** a held boot generation had an unversioned system-meta dependency, while later Plymouth and theme generations had independent acceptances and used an already supported interface. A separately held stereo layer had a pack requiring its newer interface, so that pack stayed held.

A later accepted recipe may be the sole exception to an otherwise frozen build commit when the coordinator explicitly authorizes it.
Bind the recipe directory by Git tree equality between the accepted main commit, the staged build record's commit, and the preparation tree.
Keep every other recipe at the original freeze, and regenerate metas when the new package changes minimum versions.
Do not infer whole-tree provenance from one matching recipe directory.

A new preparation gets a fresh copied pool and manifest; the blocked pool is evidence, never its input.
Checks reused across preparations need an explicit list of equal input hashes, including their tools and published comparison inputs.
Rerun every installed-system check from the retained published baseline.
Only after the new manifest verifies may the old pool be removed by its literal path under the coordinator's cleanup authorization.

Before planting conffile edits, retain the published baseline's verification output and the relevant original file hashes.
A unique appended test marker distinguishes the proof's edit from an already changed baseline file.
Compare baseline and upgraded problem rows side by side, separating explicit planted edits; a coordinator-approved baseline comparison does not waive any newly introduced problem or alter the verifier.
Run deep verification with HTTPS access to the originals it needs, and retain exact download failures when those originals are unavailable.

## A successor audit must distinguish same-version source branches

- **Symptom:** a newer accepted application catalogue lacks an entry and helper found in an older staged package, even though every comparison with the published package passes.
- **Cause:** two different staged source closures use the same version; only one was merged into the build tree. A review acceptance that explicitly holds the code merge does not make the other closure a release predecessor.
- **Fix:** identify each predecessor by descriptor hash and stage path as well as version. Read its acceptance and merge condition, compare the catalogue entries and authored helpers, and name an excluded unmerged branch separately. For accepted predecessors, explain every lost feature; a higher version or a retained filename is not proof of preservation.
- **How found:** comparing catalogue dictionaries showed one missing entry and the native source comparison showed its missing verifier helper. The journal explicitly held that branch's merge, while the accepted same-version branch's entries survived exactly.

Read native authored files and embedded upstream trees as well as quilt series: an unchanged one-patch series can accompany changed application code in the original component.
A file moved between packages needs a comparison at its new owner; retain an assertion that every former association or entry survives there.
Treat a source changelog containment test as a lead for review, not a feature-preservation verdict: qualification headers, combined source packages and held outputs can change the generated history.

For a whole-pool Lintian delta, group increased contexts by tag and demonstrated cause, retaining counts, one concrete example, and the owning fix or false-positive evidence.
A common helper's purge/error handling and a valid space-containing conffile can require reading the actual helper or an isolated dpkg unpack to explain a diagnostic.
Name new error-severity findings in edition-authored packaging at the top of the hand-back even when the functional gates pass; a classified finding is not a corrected package.

A patch-reader size cutoff can silently make two large patches compare equal as two missing values.
Read and hash every member named by `series`, and fail if any member was not read; a large combined edition patch is still a patch that must be compared.
The symptom was identical `missing` hashes for different generations; removing the reader's cutoff exposed the actual depth-conversion and cache-invalidation changes for review.

## An archive failure whose last attempt hides a missing compute repository

- **Symptom:** the link gate's final APT error names two mutually conflicting NVIDIA driver-lock packages while checking a CUDA application's debug companion.
- **Cause:** the supplied archive universe omits the vendor's compute repository. The no-lock and each single-lock solve already fail because the CUDA runtime dependency has no candidate; the final both-lock combination reports its own conflict and masks that first cause in the top-level message.
- **Fix:** preserve every policy-attempt log and the application's actual dependency control. Bind the edition's intended compute repository, public signing key and architecture restrictions from its source-package/ISO configuration, retain the edition's display-driver locks, and rerun the complete archive gate against the corrected explicit universe. Do not waive the failure, request both locks, or classify the application as broken solely from the last attempt. Follow the preparation's explicit failure contract: when archive correction is authorized, bind the missing installed-system archive and rerun from input one; report the exact gap and unchecked tail until that run completes.
- **How found:** the first three solver logs said the exact CUDA runtime had no choices; the archive configuration listed Debian, multimedia and distribution repositories but no vendor compute archive. Reading the policy solver showed that it raises its last unsuccessful alternative, not necessarily the most informative one.

Bind the compute archive from the frozen `packages/sparky-stereo-cuda-repo` recipe: `sparky-stereo-cuda.sources` supplies the HTTPS URI, exact-path suite `/`, no components and `Architectures: amd64`; `cuda-archive-keyring.gpg` in that same recipe supplies Signed-By.
Record the Git commit and hashes and verify that the working files equal that commit; do not obtain another key or disable archive signature verification.
The gate already reads package-shipped policy: compare `91sparky-stereo-cuda` with the recipe's records and `10sparky-stereo-nvidia-driver-lock` with its version-generated template, then retain their package owners and hashes in the solve evidence.
The frozen ISO installs the CUDA source package and main driver lock together before reading the vendor archive; the alternative legacy lock remains mutually exclusive, as the unchanged gate's policy solves require.
No additional preference record is needed to repair a missing archive entry.

- **Symptom:** adding the vendor URL alone leaves the provenance and installed-system policy of the proof unclear.
- **Cause:** archive sources are explicit gate inputs, while pin files come from the supplied binary packages; neither should be inferred from the other.
- **Fix:** bind source, architecture, public key and shipped pin records separately, preserve the unchanged pool manifest before and after, and hash the retained checks' inputs when their reuse is explicitly authorized. Read every solver attempt on a later failure; correct another missing installed-system archive before blaming a candidate package. A real candidate dependency or load failure requires the authorized source-family hold and a new preparation with its dependent proofs.
- **How found:** the frozen source file specified a flat amd64 archive, the public key matched the published source package byte for byte, and both CUDA and generated driver-lock pin records matched the frozen recipes. The earlier failed solver already recorded those pins, proving that the omitted archive entry was a separate configuration gap.

An unchanged pool does not freeze an external archive's next signed index.
Keep the index hashes alongside the pool hash and distinguish a newly selected upstream dependency from a changed edition binary.

- **Symptom:** after restoring the missing compute archive, the full gate fails on its first GUI package, earlier than the original CUDA failure.
- **Cause:** Debian testing's newly signed index advances XMLGUI and the style library to a generation requiring an icon-theme library newer than the edition's unchanged published rebuild. The edition's existing policy correctly refuses replacing that patched library with Debian's build.
- **Fix:** retain every solver attempt and both index digests, compare the unchanged published predecessor's dependency resolution, and check the required meta before proposing a source hold. A selective hold cannot repair a mismatch also present with the published desktop and no candidate packages. Name the published library's qualified-successor requirement; do not waive the gate, invent an archive rollback pin, or silently replace the edition's library. Preserve earlier authorized proofs with their exact input hashes and state their original archive scope.
- **How found:** the previous and new signed Debian index hashes differed while all pool files matched. The published GL package failed through XMLGUI too, and both published and candidate desktop metas failed through Oxygen and the style library on the same icon-theme minimum version.


When a partial Debian Frameworks transition breaks the published desktop as well as the candidate, measure the whole fork set before rebuilding.
Bind one signed snapshot for the successor builds and all index-dependent proofs, preserve every edition patch and binary source fixture, and leave a fork on its current source until testing supplies its successor.
The [Frameworks transition recipe](frameworks-transition.md) records the measurement and source-preparation traps; source preparation alone does not qualify the new binaries.

When a Frameworks transition builds past failed tests or removes a retired Debian compatibility library, use the measured cases in [Frameworks transitions](frameworks-transition.md); the build exit alone does not qualify its tests, and every removal needs its own evidence.


### Published predecessors during an archive transition

If the candidate resolves but its correct published predecessor fails against newly migrated Debian packages, retain every solver attempt and the previous sibling snapshot.
The explicit dated-view rule in the build toolkit’s `lean/archive.md` qualifies the predecessor against a publication-time snapshot of the implicated archive; unrelated archives may retain the candidate’s exact signed indexes only with the checked search-evidence exception.
It checks the external solver cause, archive identities, publication cutoff, signed Packages hashes and absence of candidate packages itself; the candidate never leaves its current frozen view.
The complete recipe, refusal controls and third-party archive requirement are in [Debian Frameworks transitions](frameworks-transition.md#a-repaired-candidate-does-not-repair-its-historical-comparison).
The symptom was a successful 6.32 candidate followed by a 6.30 predecessor blocked by Debian's new XMLGUI minimum; reading the full solver chain identified archive movement rather than a candidate regression.
A baseline image assembled after publication can already contain newer third-party indexes, so retain the signed publication-time metadata when the round goes online.


**Required supply-chain input:** run the candidate qualification with `--archive-evidence` and keep the resulting per-architecture InRelease, Packages, public keys, archive-view.json and SHA256SUMS beside the selected pool's evidence.
The publication script must copy that directory into the round's supply-chain record and run `sha256sum -c SHA256SUMS` in every architecture directory before publishing.
Retain the successful whole-pool gate result as well: an authenticated input snapshot alone is not a passing comparison.
A prior round without these retained archive views cannot supply a dated baseline for an archive that subsequently moves, unless an independent signed snapshot service supplies it.


### A published binding with no usable publication-time baseline

- **Symptom:** the predecessor gate stops on a taken package's old Perl binding, whose required virtual ABI is absent from both signed archive views; the last policy attempt instead names two conflicting driver locks.
- **Cause:** the old package was already uninstallable when published. Judging the failed relation by its owner confuses the taken binding with the external provider it needs.
- **Fix:** use the toolkit's checked publication-time absence rule, never omit the predecessor by hand. It checks concrete names and Provides across both complete edition sets and both authenticated archive views, binds a mandatory dependency path from the requested predecessor, and retains every solver attempt. Providers owned by either edition still block. A predecessor that solves at publication keeps that real baseline. An external name absent then and now yields no usable baseline only after both real solves fail; every candidate link and start result must then pass without comparison allowances.
- **How found:** the first three solver logs named the retired ABI; the fourth ended at a policy conflict. The previous control and both authenticated Packages indexes showed the old relation and the newer runtime's actual Provides. The candidate's exact dependency qualification succeeded with that newer ABI.

Run the full pool with `--collect-predecessor-stops` to collect uncovered eligibility failures once, rather than discovering one per multi-hour invocation.
The mode still exits 1 while any uncovered stop remains; it retains every input, complete solver lines and archive evidence in `predecessor-stops.json`.
Keep `uninstallable-predecessors.json` and the summary's separate list headed `published predecessor not installable at its publication`.
Describe each such input in the round's description as repairing already published breakage; never call the old baseline passing.
The main publication invocation must carry the same historical-view options and evidence bindings; a stage list alone does not select this proof mode.

A provider-presence inventory is not a second policy grammar check for every unrelated signed archive entry.
Keep legacy mixed-case virtual names and compact version syntax literally; a signed third-party office alias exposed this during the full-run startup.
Count a transitive missing dependency only when the required path has no alternate virtual provider, and retain the named path as evidence.
The complete archive solver remains authoritative for installability.


### Exact companion dependencies and a completed failure inventory

- **Symptom:** a checksum-correct, exactly reproduced style package fails candidate qualification because it requires an older exact version of its GTK companion; its menu-bar variant fails through the same relation.
- **Cause:** separate accepted source generations retain an exact cross-source dependency that the selected newer companion cannot satisfy. Receipt equality proves reproduction, not compatibility of the assembled cohort.
- **Fix:** retain all policy-attempt logs and read the actual binary controls of both selected and published style packages. Trace direct dependents and Recommends before naming a source-family hold; leaving out only the new style does not help when its published predecessor has the same old exact dependency. Reconcile that source family through the authorized successor or new-preparation workflow, without changing the already accepted archives or weakening the solver.
- **How found:** the first three policy attempts named the old exact companion version, while the fourth reported the independent driver-lock conflict. Scanning the complete pool's relations found the dependent menu-bar source and the base look's recommendation; the published style control retained the same exact dependency.

Compare the installed proof baseline with the image builder’s default Recommends closure as well.
A transaction on a baseline that omits the incompatible recommended companion does not prove that the image’s requested combination upgrades.
Record the absent packages beside the image-install command and binary relations; do not call a recommendation successfully installed merely because apt can omit it.

`--collect-predecessor-stops` collects predecessor eligibility failures, not arbitrary candidate failures.
A candidate solve or runtime failure still ends that invocation with exit 1.
When the task requires a complete failure inventory, retain that invocation and check the unvisited inputs with the unchanged gate and complete sibling universes, verifying that every invocation uses byte-identical signed archive views.
Record every invocation's input interval and exit, every failed input and all solver attempts, and assert that the union accounts for the entire selection.
Those diagnostic continuations do not turn the interrupted full invocation into a passing whole-pool proof; a corrected preparation still needs its own complete gate.

## A successor family and a bound continuation of its proof

**Symptom:** a look and its menu-bar variant require an obsolete exact GTK package version, while the round carries a compatible newer GTK theme.
**Cause:** a recipe's default version was interpolated into a dependency, independently of the GTK package's actual version.
**Fix:** read the commit introducing the pin and compare the actual theme names, colour-scheme mapping and files it protects.
If equality protects no interface, declare the oldest compatible GTK version as a minimum in the required version-definition file shared by the builders; refuse a missing definition.
Build both look successors from that committed recipe, retain every language file, and compare them with both staged and published predecessors.
Keep an unchanged GTK archive unchanged.
**How found:** the solver's first attempts named the exact pin; the original theme files and current files were equal despite independent package version counters.
The installed upgrade baseline must contain both published looks as the image's Recommends request, and prove their upgrade together with GTK, not merely an edition without those looks.

A predecessor requiring an unavailable publication-time third-party archive has `no-baseline-available` only through the gate's explicit option and checked archive search records.
The unchanged predecessor is first tried in the candidate view; any permitted successful view remains a real baseline.
A failure attributed to an archive without its dated signed index cannot use a later implicated index as a substitute.
Such a candidate gets no inherited-failure allowance and must install, link and start in full in the frozen candidate view.
The real unresolved-library regression control must remain red.
This is not the separate class proving a missing provider in both extant views.

A changed gate rule requires the full toolkit suite on the exact new code, plus a seeded fresh sample of 24 previously completed comparisons, including at least four mixed baselines and both publication-time-uninstallable inputs when present.
Use the gate's bound reuse mode, not a hand-edited passing table.
It checks candidate and predecessor hashes, original sibling inputs, authenticated signed views, code, prior result hashes and the suite record.
Changed inputs, their transitive dependents and inputs without a passing prior result run fresh.
The sample's findings, notes and predecessor classes must agree before reuse is permitted.
Every input then receives one fresh or reused verdict with its binding, and exit zero requires every row to pass.
Retained signed indexes must be restored and authenticated without updating the public archives during either the link proof or installed upgrade; updating the local candidate index must leave those public bytes unchanged.
Record old/new pool digests, the replaced source sets, complete verdict, sample seed/list, exact archive evidence paths and all publication-copy inputs.

### Frozen installed indexes must cover installed foreign architectures

**Symptom:** the expanded installed proof keeps back the two architectures of the stereo declaration library and Mesa, although both architecture link gates pass.
**Cause:** restoring only the amd64 proof indexes omits the i386 public dependency universe; copying the i386 indexes without changing the generated `arch=amd64` selectors still leaves those packages invisible to APT.
**Fix:** authenticate and copy both already-qualified views, require equal shared InRelease hashes, and expose both installed architectures for archives that support both.
Keep NVIDIA's compute archive amd64-only as its edition source declares.
Refresh only the local candidate index, checking the public index hashes before and after.
**How found:** all eight kept-back names were read before any transaction, and the source architecture selectors explained why the copied i386 Packages files were unused.
Retain failed setup attempts separately; do not change pins, package archives or the frozen public view to satisfy the solver.

### Frozen source selection must preserve packaged files

**Symptom:** the installed transaction and ordinary verification pass, but deep verification reports `LCCHANGED` for the edition's deb-multimedia source file.
**Cause:** the proof replaced APT's source selection by deleting every sourceparts file, including a packaged Lean payload; a baseline image captured after that setup inherited the missing file.
**Fix:** preserve packaged source files and select a private sourceparts directory through an unowned proof APT configuration file.
Expose the proof's local edition source there and keep the authenticated public view in the generated main source list, with the same archive keys, architecture selectors and pins.
If a derived baseline already contains the setup mutation, restart from the original published baseline and install its recommended companion packages again before applying the corrected setup.
Rerun the complete installed transaction and deep verification; never exempt the source path or weaken the verifier.
**How found:** deep verification named the one extra path, the stopped container had no such file, and the original published image still held it; the setup's unlink loop and derived-image timing explained the difference.
Keep the failed attempt and compare the public index hashes after the corrected proof as well.

### A migration between preparation and publication

A successful frozen-view qualification is not evidence for a later live archive.
If the official fresh-install check finds a new Frameworks dependency floor, authenticate a new snapshot matching the live InRelease, measure every fork counterpart and every candidate's installability, and prepare the necessary successors with all edition patches.
The [later-migration procedure](frameworks-transition.md#a-later-migration-before-publication) covers disabled Debian patches, installed public-API controls and catalogue source mapping.
After the successor pool is complete, rerun fresh installation and the installed upgrade against both the frozen view and live Debian, recording the live minute and all retained signed indexes.
A library loaded throughout the desktop still needs the real-machine program-start bench before acceptance.

During that measurement, compare failing test packages and Multi-Arch pairs with Debian's own packages in the identical signed view before choosing a rebuild.
The [archive-failure controls](frameworks-transition.md#separate-archive-failures-from-a-forks-regression) distinguish an inherited dependency conflict, task reachability and a base-library fix's actual retirement condition.
Keep every finding in the inventory; report-mode exit zero is completion, not qualification.

### A fresh whole-pool run still uses the frozen indexes

Symptom: a full rerun has no reusable comparison records, but the default archive initialization updates every third-party index even when Debian has a dated URL.
Cause: a dated Debian source does not freeze the other archives; the retained-index loader was exposed only through the reuse path.
Use `check-link --archive-view CONTEXT --previous-archive-view DATED_CONTEXT` for a fresh full comparison on the retained candidate and publication views.
These are the Archive context directories containing metadata.json and state/lists, not a bare Packages file or an unverified mirror.
The loader rechecks source configuration, keys, sizes, hashes, signatures and signed Packages hashes, and the normal predecessor eligibility rules still run.
The options cannot be combined with --reuse-manifest, which already binds its two views.
The failure was found while binding a replacement pool to its accepted frozen view; altered-index and genuinely broken-candidate controls still refuse it.

When copying an isolated apt universe to a different scratch path, rename its local edition list filenames too: apt encodes that URI in the list names.
Otherwise apt ignores the copied local Packages and says the edition metas cannot be located, even though the public indexes are present.
Keep the signed public index bytes unchanged, update the private local URI/list names together, and read the solver's complete lines before attributing that setup failure to a package.

### Prepare both link-gate views and check a small cohort

1. Start with the signed InRelease used by the accepted live proof.
   Read the timestamps in the Debian Snapshot calendar and fetch the testing InRelease from each relevant capture.
   Verify its signature and compare the full signed file's SHA-256 with the proof.
   Bind every Packages file to its signed SHA-256 and size.
2. Take the predecessor cutoff from the record of publication.
   Require both the Debian Snapshot capture and its signed Date to fall at or before that instant.
   For deb-multimedia, SparkyLinux and any vendor archive, check the published round's retained archive evidence first.
   Verify its checksum manifest, reauthenticate the selected InRelease and Packages with the archive key, and record their signed dates.
   Keep the official-mirror, retained-baseline and archive-search results with their hashes.
   Use the checked mixed-view policy only for an archive whose dated signed copy those searches could not find and whose indexes are unrelated to the solver failure.
3. Give the candidate and predecessor source lists the same archive order, suites, components, architecture restrictions and keys.
   Verify the fingerprints of retained public keyrings against the installed public keyrings.
   Keep the dated Debian and third-party indexes under their original repository URIs so APT still knows where to obtain the payload files.
   Supply both retained Archive contexts through `--archive-view` and `--previous-archive-view`.
   Each context needs `metadata.json` with its exact source configuration and key hashes, and the saved `state/lists` files with their sizes and hashes.
   A prior round's exported `archive-view.json` gives the evidence identities for reconstructing a context.
   The retained-context loader reads `metadata.json`, checks the signed indexes again and uses those bytes to solve.
   Put one official argument per line in the round's link argument file and check that its paths agree with the source and context files before handing it back.
4. Run `PYTHONPATH=sparky-os python3 -m lean.release check-diversions POOL` from the frozen build checkout.
   Keep its report with the round. A refusal names the archive, the unsupported preinst and the payload paths at risk.
   Inspect additions with unresolved source paths before proceeding.
5. Run the gate from the frozen build commit on the changed native binary identities and their exact HR companions.
   Give it the complete applicable sibling list from each candidate and published index so each target can solve against its own edition.
   Copy the tested packages by reading the files and verify the copies against the index.
   Sign the disposable subset with a throwaway key and keep it outside the public source lists so predecessor qualification can check for candidate contamination.
   Run with read-only access to the frozen pool and live tree.
   Record wall time, sampled scratch high-water mark, the gate's exit status and every solver or setup refusal.
   Preserve the small result and signed view inputs before releasing generated roots and caches.

Traps met while preparing the views:

- **Capture date.** A capture near publication can contain a Release from after publication.
  The next snapshot after midnight had an InRelease signed several minutes after the round was already online.
  Comparing both timestamps with the recorded cutoff selected the previous capture.
- **Retained evidence.** The current mirrors and an archive search can leave a dated view looking unavailable while the prior round holds signed files that meet the cutoff.
  The retained supply-chain archive evidence supplied all three examined third-party indexes.
  The proof's later local indexes had signed dates beyond the cutoff.
  Keep the searches for each cutoff and use the authenticated retained bytes whenever they qualify.
- **Disposable signature.** Generating Release inside the tree can make the indexer hash a partially written Release.
  Generate it beside the tree, move it into place and sign it there.
  For a cleartext signature use a real output path with `sqv` and check the signed Packages hash and size.
  The comparison of generated and verified Release fields exposed the self-entry and a final line-ending difference.
- **A data-only root reports a conffile collision.** The `sparky-stereo` desktop meta's gate run exposed a collision between the Debian conffile and the edition symlink at `/etc/initramfs-tools/update-initramfs.conf`.
  The exact boot preinst used a literal variable and moved the owning package's pending `.dpkg-new`. The parser supported only the literal loop and direct commands at the time.
  A disposable two-archive `dpkg --unpack` established the diversion, the symlink and both retained conffile hashes.
  Keep the measured package script and extend the gate with the exact script form and a [dpkg-divert oracle test](../../lean-code/references/diverted-files.md#diversions-in-the-link-and-start-gate).
- **An unmodelled preinst may still ship the source name.** The link gate originally found the collision only when assembling the large meta root.
  Comparing each unmodelled script's diversion sources with its data members identified the collision risk in seconds.
  Run `check-diversions` before starting the long gate. The command records modelled and unmodelled scripts with reasons and exits nonzero on payload overlap or an unresolved addition.
  An unmodelled script gains no filesystem operation from this check. The qualified link run still checks collisions in each assembled root.
- **A signed download ends early.** The Chinese LibreOffice help archives returned HTTP 200 and the expected Content-Length from Debian Snapshot, then closed after only part of the body. The gate refused the size and SHA-256 mismatch. A separate HTTPS request reproduced the truncation while Debian's mirror supplied the exact bytes.
  Verify the full size, SHA-256 and package identity against the frozen signed Packages entry before placing either archive at its SHA-256 name in the gate's disposable cache.
  Resume at the first refused input with the same build, views, sibling lists and options. Keep the initial completed verdicts and both transport records. The gate checks the cached bytes and archive identity again.

### Zero removals and a caller's shell mode

Symptom: a fresh task plan resolves thousands of installs and zero removals, then the wrapper exits without a FAIL verdict before installing anything.
Cause: the proof helper counts removals with `grep -c`; zero matches prints zero but returns status one, which a new caller's `set -e` treats as fatal.
The existing upgrade caller already disables errexit around helpers that call `fail` explicitly.
Invoke these explicit-failure helpers in a checked conditional, or use their established caller mode; retain every install, kept-back and removal check.
Read the helper and the complete plan before treating this shell exit as a package failure.
Keep the interrupted invocation, bind the unchanged planned root and signed indexes, and resume the actual transaction only after the same helper passes.
Do not confuse a fresh install command's unrequested bootstrap upgrades with solver-kept packages: name those packages and their versions separately, and still read back every selected edition target exactly.

### APT's versioned terminal assignment is not its request chain

Symptom: an old runtime and its debug companion stop as failures inside the candidate set, although their missing external ABI names exist in the authenticated publication-day view.
Cause: the terminal-owner parser does not recognize `package:architecture=version`, and an unanchored search for `   2. ` can select a nested second request-chain item before the actual second conflicting assignment.
Read the top-level assignment anchored at the start of its line, accept the optional version after the architecture, and use that same terminal section for the unmet relation.
Keep the complete request chain for archive attribution; fixing the terminal parser does not allow a later implicated third-party archive or an edition-owned provider.
The dated solve must still succeed, or the existing checked unavailable/uninstallable-baseline rules must apply; no inherited-failure allowance is invented.
The defect was found by reading every policy attempt and both signed provider indexes, then reproducing the versioned owner and nested chain with a concrete-library transition fixture.
Keep the old full-run evidence, run the whole toolkit suite on the corrected code, and certify any reused comparisons through the bound seeded-sample procedure above.


### A diversion-removal message is not a removed package

**Symptom:** the real-install log checker reports a removed package named `'diversion`, although apt planned no removals and the installed package database retains the baseline names.
**Cause:** `dpkg-divert --remove` prints `Removing 'diversion of /PATH to /OTHER by PACKAGE'` during merged-/usr maintainer-script cleanup.
A parser that takes every line starting with `Removing ` as a package removal confuses that message with dpkg's `Removing PACKAGE (VERSION) ...` record.
**Fix:** exclude the complete known diversion-message form, then apply the unchanged package-removal allow-list to every other `Removing` line.
Unknown lines must still fail; a broad exclusion of removal output would hide real package loss.
Run the proof-check suite with diversion-only, diversion plus an unlisted architecture-qualified removal, diversion plus an allowed removal, and unknown-output controls.
Read the before/after package database as well as the simulation and real log.
**How found:** every rejected line named a diversion path, not a package/version pair; two positive fixtures failed under the old parser and passed after the correction, while real unlisted removals remained red.
If apt completed before this post-install parser stopped, keep the exact transaction log and failed checker output, then resume the checks on the same installed root.
Do not reinstall or discard the completed transaction merely to work around a log-parser fault.


### Deep verification needs the bootstrap's exact originals too

**Symptom:** the real fresh task transaction succeeds, but deep verification prints `NODEB` for an unchanged bootstrap package whose exact version has left the candidate index.
**Cause:** installing the tasks need not upgrade every package already present in the base image, while the verifier needs the original archive of the installed version.
Name these unrequested bootstrap upgrades separately; do not upgrade them merely to erase a verification finding.
**Fix:** recover the exact original into the disposable APT cache, independently authenticating its dated InRelease, archive key, signed Packages hash, binary SHA-256 and package/version/architecture.
Keep that original-only archive evidence separate from the candidate's solver view; neither the installed files nor the candidate indexes change.
Retain the complete first verification output, then rerun the unchanged verifier with the authenticated original available.
The whole-pool rerun must provision the same original when that bootstrap version remains installed.
**How found:** the verifier's download error named the old bootstrap version, the installed readback confirmed it, and its signed historical Packages record bound the recovered archive.

## Lessons from the preparation after r1123a (queue row 933, 26 November 2026)

### The take list reads both journal forms
- **Symptom:** a take list built from the journal's `- TIME, NAME: ... ACCEPTED` lines misses accepted stages, among them a console, a dpkg-stereo and a libXext that waited for "a later round".
- **Cause:** acceptances are also written as section headings (`## TIME  813 ACCEPTED and staged: ...`); the bulleted form is only one of two.
- **Fix:** match both (`^(?:- |## )TIME`) and list every acceptance since the published round froze; then rule each one by name.
- **How found:** the parser saw no acceptance between 19 and 23 November; a plain `grep -n ACCEPTED` over those lines showed the headings.

### A row marked published is not proof that its package is
- **Symptom:** a staged-looking generation (an accepted milestone) is newer than every published record, yet its row is set `published`.
- **Cause:** the round's "rows set published" step matched rows against the pool by script, and a row whose package never entered the pool was set published anyway.
- **Fix:** for every accepted generation newer than the published index, read its row status and the published index together; a mismatch goes to the coordinator, never silently into or out of the take.
- **How found:** the published inventory had no record of that source at all, while the journal had its acceptance with a closure check.

### An edition package's changelog has one entry; prove succession by its recipe commit
- **Symptom:** the winner's `debian/changelog` does not contain the predecessor's version for the console, the boot package, the looks and other native edition packages, so a changelog containment test says "not carried".
- **Cause:** their recipes write a fresh one-entry changelog; their history lives in the build tree.
- **Fix:** read `recipeCommit` from both build records and require `git merge-base --is-ancestor PREDECESSOR WINNER`; a commit from before a history rewrite is first mapped through the commit map the rewrite kept. A held generation's commit that is not in main at all is evidence that its work is not in the winner.
- **How found:** every "not carried" row of the changelog test came from a native package; the build records' commits, mapped, were all ancestors.

### A held branch's patch inside an accepted successor
- **Symptom:** an accepted package (kpipewire +stereo3d10, row 81) is the newest generation, but its patch series carries the patch of a predecessor whose branch is held (row 740's `order740-hevc-packing.patch`).
- **Cause:** the successor's recipe takes the held predecessor's source as its base.
- **Fix:** read the winner's `debian/patches/series` against each held predecessor's; when a held patch is inside, name it first among the disagreements with what holding the winner would cost (here the Throw package requires the winner's library version), and let the coordinator rule.
- **How found:** the succession table showed the held predecessor's changelog entry inside the winner; the series showed the patch.

### translations-shipped.py: a missing SOURCES row, and old gaps beside new ones
- **Symptom:** exit 2 (`not in SOURCES, so no package to look in`), and dozens of `FAIL` lines for packages the round does not even take.
- **Cause:** new catalogue patches were added to `sparky-os/translations` without a SOURCES row; the test also reports every published package that never carried a later catalogue backfill.
- **Fix:** add the rows (a test-table change, committed on the lane branch), then run the test twice, once with the take as `--cohort` and once with an empty cohort over the published tree, and compare per patch: a taken package fails the round only when it lacks strings the published one had or its own new sentences; an equal shortfall is an older gap, reported.
- **How found:** comparing the two runs left exactly one failing taken package, the live captions adapter with 60 of 300 strings.
- A package the test does not cover (no registered patch or JSON catalogue) is read directly: `dpkg-deb -c` for `.mo`, `.qm` and `lang/*.json`. Kaption and captiond shipped none.

### A removed HR blob is read through the lc manifest's `sha_hr`
- **Symptom:** the file-by-file comparison leaves `usr/share/dpkg-stereo/hr/PKG/ARCH/HASH.xz` lines as removed paths needing explanation.
- **Cause:** HR blobs are named by content; a changed authored file gets a new name, and a file that is no longer projected needs no HR copy.
- **Fix:** in the published package's `usr/share/dpkg-stereo/lc/PKG/ARCH.json`, find the entry whose `sha_hr` is HASH; the successor's manifest must list that `path` again (renamed by content), or its entry must say `unchanged` (shipped whole), or the authored file itself left for a reason the successor's changelog or recipe history gives.
- **How found:** 59 of 78 unexplained removals resolved this way; the remaining 14 were read one by one (a list moved to System Settings, `/etc` files shipped as defaults so a person's edit is kept, a check moved into the Problems engine, a README compressed by `dh_compress`).

### Repairing a standalone source's missing buildinfo and changes
- **Symptom:** `requalify-script.sh` stops in `dpkg-buildpackage` with `unmet build dependencies: build-essential:native node-acorn nodejs python3-yaml`; after that is fixed, the repaired record says `recipeDirty: true`; then `metadata.py` reports `not bound by stage SHA256SUMS` for copies of the originals.
- **Cause:** the reconcile Dockerfile lacks the standalone source's build dependencies; the record reads the clone's dirty state (an uncommitted test change); `metadata.py` walks the whole repair folder.
- **Fix:** add those four packages to the builder image; run every build step from a clean checkout of the frozen commit (commit lane changes on the lane branch first, then `git checkout --detach FROZEN`); keep the originals for comparison outside the repair folder.
- **How found:** the first container's log, the record's fields, and the closure check's message, in that order. The repair gave equal payloads and controls for both sources; one pair of archives came out byte-identical, the other only member-equal.

### An index-only candidate tree for check-installable.py
`check-installable.py --unsigned` reads only `dists/` and simulates, so a preparation without a signed tree can give it one: the published binary indexes with each pool binary replacing the record of the same Package and Architecture, and a Release that keeps the published Origin, Label and Codename (a few lines of Python; row 933 kept one beside its report).

### Compare the candidate with the published tree

Run `check-installable.py` in report mode on both trees with the same APT version, engines, profiles and public archives.
Verify the published tree's signatures and let each tree supply its own shipped pins.
Keep the two metadata files, the per-profile solver logs and the signed public `InRelease` and `Packages` files.
Compare public index hashes **per profile** before attributing a difference to the candidate.
If an archive moves, replay each tree against the same authenticated external indexes for attribution and record a fresh live qualification separately.

Join `installable.tsv` by package, architecture and profile, keeping both exact edition versions and the dependency path.
Read the twin rows by package and profile and read collateral rows by origin, package, exact external version, architecture and profile.
A candidate-only report row can be a new package or a new query selected by the checker's policy search.
Run the exact published-side query when an absent row leaves the old solve unclear.
Keep solver and static results together and use APT's actual simulation as the installability verdict.
An inherited failure still needs its owning fix before publication.

- **The same URLs and suite names can yield different package sets.** Debian testing refreshed between profiles in one candidate run.
  Reading the signed release dates and recorded hashes showed that base used the previous day's testing release while NVIDIA and arm64 used the next release.
  Authenticate each retained release with its public key and check the signed size and hash of each Packages file against the recorded profile.
  Simulate with the same public files and the published edition's own signed indexes and pins.
- **A CUDA consumer can fail without the vendor archive and install with it.** The two solver profiles differed, and the pinned firmware and CUDA runtime appeared in the vendor Packages index.
  The ISO installs `sparky-stereo-cuda-repo` before reading the vendor archive and Hardware Setup installs it with the selected driver lock.
  Cite those paths and retain the solver result using the shipped archive and pins.
  For the legacy NVIDIA branch, apply its active preferences before the solve. Asking APT to install a lock package in a simulation does not load the package's preferences.
- **The first profile can spend minutes indexing before it runs an install simulation.** The static checker was walking thousands of literal package selectors for every external package.
  Timing the original and indexed matchers over the same 900 Debian entries with the published pins produced identical decisions and cut that step from 3.244 seconds to 0.026 seconds.
  The indexed matcher preserves pin-record order and keeps the existing glob and regular expression matcher. APT still runs every requested simulation.
- **A collateral row can say the candidate is from another archive even when the edition introduced the failure.** The report attributes only the direct exact relations that triggered the query.
  Exact-version APT simulations passed on the published tree for 29 candidate-only arm64 rows. The candidate's full solver paths led to the newly preferred edition Kirigami data package in 27 of them.
  Compare the exact target and read the full conflicting assignments before attributing the failure. If two archives offer the same package and architecture, preserve a separate exact-version solver log for each.

When Debian replaces a shared-library package, read the first hard dependency the solver cannot satisfy and identify its new provider from today's signed index.
Check the successor's source and development package as well as the new runtime name.
Rebuild the owning edition source with its existing patches and let the shlibs machinery emit the rebuilt binary's dependencies.
Compare all output binaries with their predecessors, retain the whole source closure and Lean Code evidence, and repeat the exact install and live full upgrade before the round takes it.

### An architecture-independent data package overrides a native cohort

- **Symptom.** Exact Debian Kirigami dependencies fail on arm64 after the edition adds `libkirigami-data`. KRDC fails with the same data mismatch.
- **Cause.** The edition's data at priority 1001 outranks the Debian data required by the only native libraries on arm64.
- **Fix.** Regenerate `sparky-stereo-only-ours` with `make-only-ours.py` from the candidate's architecture indexes. Use the generated architecture selectors to prefer edition data where its native binaries ship. Check the preferences extracted from the resulting package against the preferences used in the proof. Take an architecture-specific successor with its own complete source closure and preserve another architecture's existing source closure if that binary is still taken.
- **How found.** On 27 November 2026, exact APT simulations using the same signed public indexes passed 30 of 32 arm64 requests with the regenerated pin, including all 27 Kirigami regressions. Both exact edition amd64 controls also passed. A metadata model of a matching arm64 edition build passed 16 of the 32 exact requests and left Debian's exact Kirigami requests blocked. The model measured version selection without compiling an arm64 binary.

### Foreign test packages and LLVM OpenCL twins

- **Symptom.** `libglib2.0-tests:i386` fails in an amd64 universe, or APT rejects an amd64 plus i386 pair of `mesa-opencl-icd` at identical versions.
- **Cause.** The GLib tests pull in the Python D-Bus stack, whose amd64 and i386 packages conflict. The two Mesa ICDs pull in conflicting `libclang-cpp21` packages.
- **Fix.** Ask for the GLib test package in a native i386 universe and each OpenCL ICD on its own. Check the supported paths that use foreign-architecture packages and their dependencies. The checker retains the failing solve and marks it designed only for the named conflict. An individual install failure or a twin at mismatched versions still needs its own repair.
- **How found.** On 27 November 2026, the native GLib i386 simulation and the separate ICD requests passed. The archive's reverse dependencies and the Steam, Wine32, DXVK Wine32 and Lutris simulations showed no dependency on the two OpenCL ICDs together. The i386 GLib build recipe states which libraries those gaming routes need.

### A legacy NVIDIA package resolves only after the hardware setup's policy transaction

- **Symptom.** The base profile cannot satisfy the EGL epoch on NVIDIA 580. A CUDA profile can still select the 615 dependencies.
- **Cause.** The base omits NVIDIA's archive. The general CUDA profile loads the open-driver lock and the CUDA repository, and the 580 route adds a separate lock ahead of the open lock.
- **Fix.** Read the exact legacy lock package and replay each rejected exact-version request with both preferences files active. For the legacy DKMS request, also check that APT selects the edition's matching `nvidia-kernel-support`. Count a failure as designed only after that exact solve passes.
- **How found.** The NVIDIA Hardware Setup performs the lock and archive installation before the driver transaction. The round's 27 November 2026 controls selected NVIDIA's EGL packages at `1:1.0.6-1` and the edition's 580 kernel support with the legacy lock active.

### A runtime transition changes the generated dependency name

- **Symptom.** The installed edition's ananicy-cpp still requires `libspdlog1.15-fmt11` after testing replaces the provider.
- **Cause.** The old binary carries the dependency chosen by shlibs at build time. The new Debian package `libspdlog1.17` provides the fmt-specific dependency `libspdlog1.17-fmt12`.
- **Fix.** Rebuild with today's development packages and the source's existing recipe. Inspect the emitted `Depends` with `dpkg-deb -f` and the binary's `NEEDED` entries with `readelf -d`. Supply the recipe's signed Lean archive configuration and each edition-only dependency as a checked sibling for the link gate.
- **How found.** The exact archived package failed under APT. The 27 November 2026 rebuild linked `libspdlog.so.1.17` and `libfmt.so.12`, and the rebuilt archive and its companions passed the Lean release and signed-archive link checks.

### A transition rebuild exposes an indirect linker dependency

- **Symptom.** FreeCAD's `Import.so` fails to link with undefined TBB task group symbols while rebuilding for Debian's new MED library.
- **Cause.** Open CASCADE's headers enable `HAVE_TBB`, so `ImportOCAF.cpp` calls TBB. The Import target's link command leaves out the public library that defines those calls.
- **Fix.** Check the upstream file history and the known issue first. Declare the build dependency and link the specific Import target to `TBB::tbb`. Check the rebuilt module's `NEEDED` entries while retaining the undefined-symbol linker check.
- **How found.** The failed link command showed `--no-undefined` and the Open CASCADE libraries without TBB. On 27 November 2026, the patched target linked and `readelf -d` showed `libtbb.so.12`. [FreeCAD issue 33573](https://github.com/FreeCAD/FreeCAD/issues/33573)

### The Lean gate over a whole pool, and an accepted package without the mark
- **Symptom:** `python3 -m lean.release check-debs POOL/*.deb` stops with `No such file or directory: .../usr/share/dpkg-stereo/lc/NAME-dbgsym/amd64.json`; given only the primaries it stops with `matching HR documentation package is missing`.
- **Cause:** the first stop came from an accepted Debian-source rebuild (anacron `2.3-52+stereo3d1`) that never went through Lean Code: no `Sparky-Lean-Code` field, no `-lc-hr` companion, no `+lc1`; the second is the gate's own rule, a marked package must be given with its HR companion.
- **Fix:** list every primary's `Sparky-Lean-Code` field before the gate (`dpkg-deb -f DEB Sparky-Lean-Code`, skipping `-dbgsym` and `-lc-hr`); hold an unmarked one as a qualification gap (its lc1 source is made with `lean.debian_prepare`, as the Kamoso case above says), then run the gate on every remaining archive, companions included.
- **How found:** the two stops in that order, then the field listing, which named one package of 432.

### A library successor that breaks an edition package pinned to Debian's version
- **Symptom:** case b (a fresh install of `sparky-stereo` and the developer tasks) stops at once: `Reached two conflicting assignments: pipewire-bluez5-codec-aac ... Depends libspa-0.2-bluetooth (= 1.6.9-2)`, while every closure, version and translation check of the take passed.
- **Cause:** an accepted PipeWire rebuild (`1.6.9-2+stereo3d1+lc1`) replaces `libspa-0.2-bluetooth`; the edition's own published AAC codec was built against Debian's library and names it at an exact version; `sparky-stereo-hardware-support` Depends on the codec, so the whole edition cannot install.
- **Fix:** hold the library's source and every taken package that requires its version (Kamoso here), keep the published codec, and name the owed successor: the codec rebuilt against the new library, in the same round as it. Search the published index for every `(= VERSION)` relation on a binary the take replaces before the proofs: `grep -B20 '(= OLD_VERSION)' Packages` over the published binary indexes, or `check-exact-pins.py` with the published index and the pool's index as `--edition` layers (below, row 944).
- **How found:** the solver's chain in `e1-install.log`, then the codec's record in the published index (`+lc1`: ours, not deb-multimedia's).
- **The same pin when Debian moves (row 933, the same evening):** case e passed at 20:00 UTC on Debian testing's 14:09 index; at 21:21 its first check failed, `FAIL simulated dist-upgrade: packages are kept back`, eight PipeWire packages, 0 Remv. Debian's next testing index (signed 20:15 UTC) had migrated PipeWire 1.6.11-2, and the published codec still says `libspa-0.2-bluetooth (= 1.6.9-2)`, so apt keeps PipeWire back on every installed edition rather than remove the codec. Found by `apt-get -s --solver internal -o Debug::pkgProblemResolver=1 install pipewire` on the base with the live lists: `Broken pipewire-bluez5-codec-aac:amd64 Depends on libspa-0.2-bluetooth:amd64 < 1.6.9-2 -> 1.6.11-2 > (= 1.6.9-2)`, then `Fixing ... via keep`. The round's own content is then qualified on the base's dated view (proof-common.sh's `E_FROZEN_PUBLIC_LISTS`: the public lists the base read, only the edition's sources read again) beside the live run, each with its minute, and the codec's successor against Debian's new PipeWire is owed. Before a frozen-view upgrade, compare its `Inst` versions with the live simulation's: a version Debian has since replaced may be gone from its pool (row 933: none was; the live view only added 20 newer Debian upgrades and the 8 kept back). The dated run then passed all ten checks: 382 Inst, 0 Remv, nothing kept back, 248 newly installed, verify and deep verify clean but for the planted edits.

### The pinned package rebuilt the same day, and the watch that sees the next move (row 944)
- **See the move before a person meets it:** `sparky-os/repo/watch-exact-pins.sh OUT PUBLISHED_PACKAGES... [POOL_PACKAGES]` (build repository) reads Debian testing's and unstable's signed indexes through apt in a container and runs `check-exact-pins.py` on every exact `(= V)` pin of the edition. `FAIL testing` names the package to rebuild today; `WARN unstable` names the move that reaches testing in a few days. Run it inside an image of an installed edition (`BASE=`, `PULL=never`) so deb-multimedia and SparkyLinux count, and add NVIDIA's source with `EXTRA_ROOT=` (the published `sparky-stereo-cuda-repo`'s source file and key): without NVIDIA's index the driver's `firmware-nvidia-gsp (= 615.71.09-2)` reads as a FAIL against Debian's 550.163.01. On r1123a's published tree, 2026-11-26 22:51 UTC: 1179 exact pins, one FAIL, the codec. Run it daily (queue row 806 schedules it) and before each round with the pool's index after the published one.
- **Rebuild:** the audio skill's [AAC codec page](../../audio/references/aac-codec.md) has the recipe, the codec's own checks and the traps met on the way (the recipe could not build since 2026-11-06; the link gate needs its archive folder; the predecessor's dated comparison; the FDK library the published codec linked).
- **Compare the controls before anything else:** `dpkg-deb -f` of the successor against the published package is what showed that a build in plain Debian had swapped the edition's FDK AAC (deb-multimedia's `libfdk-aac2 (>= 1:3.0.0)`) for Debian's `libfdk-aac2t64 (>= 2.0.1)`, a second copy that `Replaces: libfdk-aac2`; every closure, link and payload gate had passed it.
- **Into the pool** as any successor: take rows for the source, the package and its dbgsym, a TAKE entry, the closure copied (never linked), `refresh-pool.sh`; the published predecessor is in the published tree, so nothing moves to the leave-out list.
- **Case e: live Debian is the verdict, the dated view beside it.** Row 944 on testing's index of 20:15 UTC: the published codec kept eight PipeWire packages back (402 Inst, 0 Remv, 8 not upgraded); with the successor in the pool, nothing kept back, and case e passed all ten checks (411 Inst, 0 Remv, 411 unpacked, 0 removed; 248 newly installed, the same list as the day's dated pass; 163 upgraded, the dated pass's 134 plus 20 newer Debian upgrades and the nine of PipeWire and the codec; the edition's FDK unchanged; verify and deep verify clean but for the planted edits).
  The dated view now keeps the successor back (1 not upgraded, `pipewire-bluez5-codec-aac`): its frozen Debian index (14:09 UTC) offers libspa-0.2-bluetooth 1.6.9-2 only. That is the expected answer once the round follows Debian's move: report it beside the live verdict, never as the verdict.

### Case e's base phase never reads the pool
`e-base.sh` installs the published edition from `/base` only; the pool is read first by `e-upgrade.sh`. When the take changes while the base installs, let the base finish and commit, and rebuild only the pool's index before the upgrade phase; stopping the base costs its whole install again.

### A new hard dependency on one alternative of a virtual the kernel decides
- **Symptom:** case e simulates hundreds of upgrades and no removal, but keeps back `sparky-stereo-cushion-swap` and a package that requires its new version; a fresh install (case b) of the same pool passes.
- **Cause:** the new version Depends on `initramfs-tools`; the edition's kernel names `dracut | initramfs-tools | linux-initramfs-tool`, dracut first, so the published edition installed with apt has dracut, which conflicts with initramfs-tools; `dist-upgrade` will not remove dracut, so it keeps the upgrade back.
- **Fix:** none in a preparation (it changes a package): name both rulings for the coordinator, a successor that accepts the alternative the kernel installs (or the kernel's order changed on purpose, with the boot proof), or a hold that follows every taken package requiring the new version. Before the proofs, compare every new `Depends` of the take with the alternatives the published kernel and metas name for the same virtual.
- **How found:** `apt-get -s install PACKAGE` in a container from the committed case e base, with the candidate source added (`edition /cand; update_edition` of the proof library), printed `Remv dracut [linux-image-... plymouth]`.
- **As fixed (row 933, ruling A):** the successor Depends on `initramfs-tools | dracut` and does its work with whichever is installed (Cushion Swap 0.3.8: see skill power-idle, "With dracut"). Prove it three ways before the pool takes it: `apt-get -s install ./SUCCESSOR.deb` in the committed case e base (0 to remove; the predecessor's `Remv dracut` is the red row), the feature on each alternative in a VM, then case e's upgrade phase again from the same base. Row 933 measured it: 0.3.7 `Remv dracut`, 0.3.8 0 to remove; four hibernate and resume cycles (swap file and swap disk, dracut and initramfs-tools); case e 383 Inst, 0 Remv, nothing kept back, verify and deep verify clean but for the planted edits.

### A native successor built inside a preparation
- **Symptom:** `lean.debian_custom` stops with `[Errno 2] No such file or directory: 'dch'`; or the recipe's own suite fails every check that reads a kept problem (`kept_problem ... 'update-initramfs -u'`), and the record's `text_en` reads "Package P: step K failed".
- **Cause:** the preparation's tool image is not a builder: the `+lc1` step calls `dch` (devscripts), the recipe's build calls `sparky-stereo-problems catalog`, and the problems engine renders a kept sentence from the package's journal catalogue in `/usr/lib/systemd/catalog`, which exists only where the built package is installed.
- **Fix:** derive a builder from the tool image with devscripts, logrotate and the published `sparky-stereo-problems`; build the recipe's `build-lean.sh` steps up to `dpkg-buildpackage`, then `lean.release check-debs` with `sparky_provenance_init` (it writes the build record; a tree with anything uncommitted under `sparky-os` is recorded as `recipeDirty: true`, and `SPARKY_PROVENANCE_REQUIRED=1` refuses only a missing fact, not a dirty tree: row 944 measured it, so commit first). Run the suite with that build's `/usr/lib/systemd/catalog/*.catalog` copied in and the tests as uid 1000 (`setpriv`), and run the predecessor's suite the same way as the baseline: a check that fails on both is the builder's, not the change's.
- **How found:** the build log's last line; then `sparky-stereo-problems keep` by hand in the builder, whose record had the generic `text_en`.

### Case e's verify fails on planted edits that moved to another package through ucf
- **Symptom:** the real upgrade passes (0 removed, 40 planted edits survived, second pass empty, audit empty), then `FAIL dpkg-stereo --verify rc=1, problems that are not planted person edits: EDITED /etc/issue (kept by sparky-stereo-console through ucf) (differs from the default ... .ucf-dist: left as it is)`, also `/etc/issue.net` and `/etc/update-motd.d/10-uname`.
- **Cause:** the proof planted those edits while base-files owned the files; the round's base-files drops them and `sparky-stereo-console` takes them over through ucf, which keeps the person's edit and puts its own default beside it. dpkg-stereo 0.1.47 reports that in a new form, and `check_verify` in `proof-checks.sh` knew only `EDITED ... (changed by the person: left as they made it)`, so a planted path in the ucf form fell into "other". The upgrade did the right thing.
- **Fix:** in `check_verify`, take `EDITED ... (kept by PACKAGE through ucf) (differs from the default ... left as it is)` as expected when its path is in the planted list, as the other forms are; rerun the upgrade phase so the deep verify runs too (it is never reached after the first FAIL).
- **How found:** the three paths were in `e2-planted.tsv` (owner base-files); `check_planted_conffiles` had passed them; `check_verify` rerun by hand on the kept `e2-verify.log` passed with the new form.

### Attribute the newly installed packages with apt's classic solver
- **Why:** case e's checks read `Inst` and `Remv` lines, so a package that should not come in at all passes them. apt 3's default solver prints no reason for a package it installs; `-o Debug::pkgDepCache::AutoInstall=1` prints reasons only with the classic solver.
- **Recipe:** a container of the committed case e base, `--network none`, the published tree and the pool as two `file:` sources (as `edition /cand` in proof-common.sh writes them), `apt-get update` limited to that sources file; then `apt-get -s --solver internal -o Debug::pkgDepCache::AutoInstall=1 dist-upgrade`. Each `Installing P:ARCH as Depends|Recommends of Q:ARCH` line is one edge; follow the edges up to a meta or a package the round takes on purpose. Check that the classic solver's `Inst` set equals the default solver's (row 933: 383 Inst, 249 newly installed, on both) before reading its reasons as the default solver's.
- **A finding:** a chain that passes through a package the round does not change, such as a carried upstream package's Recommends, brings in something no accepted row asked for.

### A Recommends with alternatives that leave out the edition's own provider
- **Symptom:** case e passes (row 933: 383 Inst, 0 Remv, nothing kept back), but the newly installed packages include a second browser, `firefox-esr` with `libevent-2.1-7t64`, on an edition whose default browser is its own.
- **Cause:** a carried SparkyLinux package keeps its upstream control fields. sparky-about 0.1.49 Recommends `firefox-esr | firefox | chromium | ... | slimjet`, 19 browsers, and the edition's Stereo Browser (`sparky-stereo-browser`, which Provides `www-browser`) is not one of them. An alternatives group is satisfied only by a package it names, so apt installs its first alternative even where the Stereo Browser is installed (measured: same `Installing firefox-esr:amd64 as Recommends of sparky-about:amd64` with and without it). The edition's welcome package Depends on sparky-about, so every upgraded edition gained Firefox ESR.
- **Fix:** keep every upstream alternative and put the provider first: `"recommendsFirst": ["sparky-stereo-browser"]` in the recipe's `upstream.json`; `build-sparky-display-tool.py` prepends it and refuses, with the reason, a control without a Recommends line, a name already in it, a Recommends of more than one group, or anything that is not a list of package names. A recipe without the field builds byte for byte as before (sparky-system: package, HR companion, .dsc and .tar.xz identical across the two builder commits). `sparky-os/repo/tests/display-tool-recommends/run.sh` builds a fixture tool through the builder (4 of 4 pass; the builder before the field fails 3).
- **Prove it:** offline, on the committed case e base, with both solvers. Red with the published package: 383 Inst, 249 newly installed, `firefox-esr` and `libevent-2.1-7t64` among them, also with the Stereo Browser installed first. Green with the successor in the pool: 382 Inst, 248 newly installed, `Installing sparky-stereo-browser:amd64 as Recommends of sparky-about:amd64` and no Firefox; with the Stereo Browser installed first, 381 Inst and nothing new for that group. Lines such as `ignore old unsatisfied important dependency on firefox-esr-l10n-de` are another package's Recommends that apt leaves alone, not installs. Then case e's upgrade phase again from the same base: row 933's newly installed list went from 249 to 248 (`firefox-esr` and `libevent-2.1-7t64` out, `sparky-stereo-browser` in) and its 134 upgrades stayed the same set.
- **Before a round:** list the take's and the published metas' alternatives groups that name another program of a kind the edition ships its own of (a browser here) without naming the edition's own.
- **How found:** the attribution above; every other newly installed package traced to an accepted row.
