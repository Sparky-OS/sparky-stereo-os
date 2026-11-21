# Debian moved a Frameworks version under the edition forks

**For publication maintainers:** measure a partial Debian testing transition, carry the edition forks onto the available source versions, and keep every proof on one signed index.

Check freshness first: written 2026-11-21 during the Frameworks 6.30 to 6.32 transition.
The four successor builds and their installed feature checks have passed; complete pool and transaction gates remain separate requirements.

## Measure the whole set

1. Keep the failed gate's complete solver attempts, public archive configuration and signed index bytes.
2. Compare a fresh solve for the published desktop with the candidate desktop, and retain `apt-get -s dist-upgrade` on the installed published baseline both with and without the candidate pool.
   Save every Inst and Remv line and every kept-back name with its dependency reason.
3. Read the signed Sources and Packages entries for every edition Frameworks fork, including forks not named by the first failure.
   A partially migrated collection is not one version: an edition KIO fork stays on its published source while testing still has that upstream version, provided its closure remains installable.
4. Bind an immutable Debian snapshot whose signed InRelease equals the live index at the start.
   Record both compressed-file hashes and the unpacked Packages/Sources hashes authenticated by InRelease.
   Use that URI for source retrieval, build dependencies and final qualification.
   If testing changes again, finish against the bound index and report what the later index would add.

## Prepare each successor

Use the source's existing recipe directory, even when it belongs to an older work's folder.
A shared preparation helper can consume a per-source manifest binding the old published descriptor, the new Debian descriptor and the exact published patch series.
Verify every component named by both descriptors before unpacking.
Start from Debian's new packaging and carry the edition's additions, rather than changing version strings throughout its older packaging.
Retain the edition changelog, symbols, dependencies, copyright additions, source-consumer preservation plan when present, and installed-test harness.
Restart the edition revision at `+stereo3d1` for a new upstream version and prove that the resulting version sorts above the published one.
Commit the recipe before building and require `recipeDirty` false in the record.

Read upstream's comparison between the two release tags before rebasing an overlapping patch.
Keep one fate for every series entry: unchanged, rebased with its exact adjustment, or redundant with the upstream commit named.
A context conflict is not evidence that the behavior is already upstream.
Copy binary test fixtures from the published Debian tarball as well as text patches and `debian/source/include-binaries`.
Prepare a fresh Lean Code source with the accepted toolkit, then run the package's tests and the existing installed red/green checks.
Compare every binary's file list with the published version, explain each removed path, and qualify the complete source closure and all publication gates.

## Traps measured during preparation and build

- **Symptom:** XMLGUI or a style library requires `libkf6iconthemes6 >= 6.32`, while the edition's policy retains its 6.30 fork.
  **Cause:** testing migrated part of Frameworks before the edition rebuilt its patched sources.
  **Fix:** measure all forks and prepare successors only on source versions testing actually publishes; neither an invented rollback pin nor replacing the fork with Debian's binary preserves the edition.
  **How found:** the published desktop failed with no candidate packages present, and the signed source index put four forks at 6.32 while KIO remained at 6.30.
- **Symptom:** the HEIF stereo reader patch conflicts at the selected-image assignment.
  **Cause:** upstream added optional library-version metadata in the same block.
  **Fix:** keep that metadata code and the edition's second/third-image selection together.
  **How found:** the upstream tag comparison identified the metadata addition; a three-way source comparison showed independent changes to adjacent lines.
- **Symptom:** a historical cleanup patch appears to delete new upstream FFmpeg test cases.
  **Cause:** that edition patch removed duplicated test functions and a duplicate main; upstream had since inserted location and Apple metadata tests in the duplicated region.
  **Fix:** remove the duplicate definitions while retaining the new tests exactly once beside the stereo tests.
  **How found:** comparing all three versions of the conflict isolated the two new functions; the prepared source keeps their declarations and definitions.
- **Symptom:** a text-only patch carry appears complete but loses stereo fixtures.
  **Cause:** source-format 3.0 quilt stores binary additions in the Debian tarball rather than the text series.
  **Fix:** carry and compare those source members and their include-binaries list.
  **How found:** listing the published Debian tarballs revealed 72 KImageFormats and 125 KFileMetaData fixture members outside debian/.
- **Symptom:** the new Debian KImageFormats packaging selects the single-binary debhelper sequence.
  **Cause:** upstream Debian produces one ordinary binary, while the edition's Lean Code step also emits HR companions.
  **Fix:** retain the edition's existing multi-binary debhelper form while incorporating the new Debian packaging elsewhere.
  **How found:** the old Debian, published edition and new Debian control-file comparison isolated that sequence change.

- **Symptom:** the source build continues after CTest reports three failures in HEIF JPEG reading, HEJ2 writing and AVCI reading.
  **Cause:** the new tests need libheif codec plug-ins absent from Build-Depends, and Debian's rules append an unconditional `|| true` through `fail_param`.
  **Fix:** add the signed archive's JPEG decoder/encoder, JPEG 2000 encoder and FFmpeg decoder as test build dependencies; remove the ignored return from the amd64 test invocation and rebuild from a committed recipe.
  Keep the test bodies and enabled formats unchanged.
  **How found:** the complete CTest summary reported 42 of 45 passing while dpkg-buildpackage proceeded; individual diagnostics named missing codecs, and apt-cache policy showed the edition already publishes them.
- **Symptom:** the transition simulation removes `libkirigamipolyfill6`.
  **Cause:** upstream Kirigami commit `38f09a837eed7e4984d744e148d0f8a2b99cfcbc` removed the unused SafeArea compatibility module after raising the Qt floor beyond 6.9.
  **Fix:** retain the exact removal, old/new controls and upstream retirement evidence for transaction review; do not confuse an obsolete Debian compatibility package with an edition dependency being removed by the solver.
  **How found:** reading all Remv lines exposed the package, and the upstream tag comparison identified its deliberate removal.

## Verify the installed forks

Reuse the owning source or row fixtures against installed headers, libraries and plug-ins, without a build-tree search path.
KIconThemes can use the existing stereo icon-loader fixture: the Debian headers reject its edition API, then the installed fork compiles and passes the same cases.
KImageFormats uses its stereo round-trip, metadata, depth and JPS-writer fixtures; verify the generated JPS APP3 and MPO MPF marks independently.
PNS belongs to the Qt PNG reader, whose existing sTER fixture must also pass; do not describe that reader check as a new KImageFormats writer.
KFileMetaData's installed fixture harness queries actual extractor plug-ins and their stereo properties.
NetworkManagerQt's existing setter and installed KCM fixture can use a private D-Bus service in a networkless container: test writes, real signals, denial, unchanged unrelated state, reload, persistence and missing-service errors.
The private service must never share the host system bus or network namespace.

A binary phase interrupted after source creation can resume without repacking a projected source tree.
Keep the original authored descriptor and compare it with independent real-clean source builds.
If a resume reports an already-marked debug archive, follow [the stale dbgsym-root lesson](lessons-2026-11.md): remove the failed debug staging roots and failed binary outputs, then repeat the binary phase and its unchanged gates.
Keep the initial failure and successful resume logs together.

## A repaired candidate does not repair its historical comparison

**Symptom:** the complete pool gate now resolves the candidate, then reports `previous edition dependency qualification failed` for its published predecessor.
**Cause:** the gate gives both sides the same frozen public index, while the previous sibling universe correctly contains the old edition fork.
The new Debian XMLGUI requires icon themes 6.32, but that historical universe pins the edition's 6.30 icon-theme build.
Rebuilding the candidate fork changes only the candidate universe.
**How found:** read all four conditional policy solves, including the first attempt without either driver lock; inspect the successful candidate resolution and the separately hashed previous universe.
The final attempt's mutually exclusive NVIDIA locks are secondary and do not explain the first three failures.
**Rule:** use the link gate's explicit `--previous-archive-config` and `--previous-published-at` mode when the previous edition cannot solve because of packages outside the selected candidate set.
The gate tries the previous edition alone in the candidate view first and examines every conditional-policy solver attempt.
Its terminal unsatisfied relation owners must all be outside the candidate set; a request chain naming the predecessor is not itself the cause.
No selected candidate identity may appear in the previous sibling snapshot or its public universe.
The predecessor view contains the same archives, components and signing keys. The archive responsible for the failure needs a signed snapshot at or before publication.
Debian uses its timestamped snapshot service, also no later than publication.
APT authenticates the InRelease files; the gate independently binds every retained Packages file to its own signed size and SHA-256 and records the metadata hashes.
An unrelated archive without a dated signed copy may remain at the candidate's exact authenticated frozen index only with the gate's per-archive search evidence: official mirrors, the retained baseline and archive searches, their outcomes and file hashes.
The gate attributes every solver-named package to authenticated archive indexes and refuses this exception if the failure names that archive.
It checks exact index equality and prints each archive's view and reason.
A mixed-view failure still blocks with the solver's package and archive names; no new pin or substituted sibling repairs the proof.

The previous exact sibling snapshot must qualify in the dated view, including its runtime libraries and applicable start probes.
The narrow Recommends case uses that same predecessor view.
Candidate solving, linking and starting stay in the candidate's frozen view, and regression checks remain in force.
Each result says which view each archive supplied and why; the summary counts dated and mixed baselines.
Without the two options the gate retains its existing behavior.
The signed offline tests demonstrate current-view red, dated green, both-views red, a post-publication snapshot refusal and an actual missing-library regression that still blocks.
Additional controls cover candidate contamination, a candidate-owned solver cause, a changed key and mutated authenticated metadata.
This rule replaces the former proof-contract impasse; it does not make an incomplete whole-pool invocation pass.

**Test-image trap:** a committed build-dependency image can retain `SPARKY_BUILD_INVOCATION` and related provenance variables.
A unit fixture that intentionally opts out of build provenance then correctly fails because it sees both modes.
Use the clean tools image from before provenance initialization for the isolated suite, preserve the failing attempt, and rerun the affected tests without changing their assertions.
The error naming both `SPARKY_PROVENANCE_OPTOUT` and `sparky_provenance_init`, followed by inspection of the image's recorded environment, distinguishes this from a package defect.


**Archive retention trap:** requiring publication-time third-party indexes can reveal that no such record was kept and the archive has no snapshot service.
The bounded search of official mirrors, retained baseline metadata and archive captures must be input evidence, not an assumption.
Only an unrelated unchanged archive is eligible for the mixed-view rule; the control in which that archive supplies a solver-named package still blocks.
Retain every candidate archive's signed InRelease and Packages bytes with the public keys and checksums using the gate's `--archive-evidence` option.
The publication step copies that directory into the round's supply-chain record and verifies the checksums before publication.
The preparation hands back its exact path and complete gate result for that wiring.
An archive that later moves needs the prior round's retained authenticated view or an independent signed dated snapshot; the exception for unrelated archives cannot replace it.
