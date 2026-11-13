# Craft Apps: contributions and review follow-through

Checked 2026-11-10 against [craft-contrib](https://github.com/storytold/craft-contrib), revision cb0d67e, and the app repositories' current rules.
Read the receiving repository again before preparing a submission: the suite changes quickly.

Inventory the organisation as well as the launcher: ArtCraft and ArtCraft-X are creative apps too.
ArtCraft's November main has both its Tauri/Three.js frontend and a new `artcraft-native` egui frontend.
Select rules by the actual repository and frontend; do not assume every app has the same renderer or gate.
Craft Status and Craft PR Review are development tools; Spark is a renderer dependency.
The launcher also lists approved community apps, currently SolidCraft and MailCraft, whose independent ownership and contribution rules remain explicit.
A catalog listing is not permission to transplant their UI or approve another third-party app.

## Working recipe

1. Read the app's `AGENTS.md`, its `CLAUDE.md` if present, the contribution files, `.coderabbit.yaml` and the called shared CI workflow.
   The core and Rust blocks come from `craft-contrib/standards/house-rules-{core,rust}.md`; local rules can be stricter.
   `craft-skills` at 2a55dce contains only its README, so it does not supply missing instructions.
2. Read the issue and every review, then search recent main, open and merged PRs for the issue and symptom.
   Keep a small table of actionable requests, the correcting commit or measured explanation, and any decision reserved to a maintainer.
   Verify a bot finding against the actual code; its suggestion is review data.
3. Restore/rebase on an explicitly recorded main revision, keep the project's module layout and tests, and run its own gate before claiming success.
   Native apps use Rust and retain their web build.
   CI belongs to `craft-common-actions`; a feature PR does not rewrite workflows.
4. Preserve the dual MIT OR Apache-2.0 licence and third-party notices.
   Check the current SPDX allowlist before adding a dependency or asset; record original/licensed assets in `ATTRIBUTION.md` with their sidecars.
   Fonts belong in `craft-fonts`.
   Edit only the contributor's own chosen credit entry; never infer another person's name or edit generated contributor statistics.
5. Prepare a short description: the concrete change, exact validation and remaining platform gaps.
   Run bots' actionable findings as regressions where they are correct.
   A static bot review is not a build or a passing gate.
6. Keep the review moving: the current core rule asks for an answer within seven days, a reminder at fourteen, and maintainer-decided closure eligibility at thirty days after actionable feedback waits on the author.
   A fix, explanation or agreed plan resets the clock; unrelated activity does not.
   Waiting on the maintainer pauses it; unconfirmed bot suggestions do not start it.
   Reuse searches and stop at a rate limit.

## Local policies differ

AniCraft’s `AGENTS.md` says crates.io-only dependencies and requires a cargo-deny gate.
At main `9e49ae93`, `deny.toml` and `docs/legal/compliance.md` also explicitly allowlist Storytold’s craft-libs repository for the pinned updater.
Read those actual policy files together; do not infer permission for a new desktop dependency from the updater’s existing exception.
A shared library existing in craft-libs does not establish that an unpublished git dependency is permitted there.
TextureCraft and MaterialCraft explicitly put shared code in craft-libs; FigCraft and Craft Anything retain no-code-sharing text.
For an edition task that explicitly requires shared engines, implement the edition library and adapters on its own branch.
Keep changes needed to meet upstream dependency or sharing policy on a separate upstream-offer branch; do not silently edit their policy or duplicate an engine merely to accommodate it.
State the boundary in the handoff before preparing an offer.
DeckCraft excludes some vendor-designed font families even when open; PdfCraft allows OFL releases under its own attribution rules.
PdfCraft’s hashed `ATTRIBUTION.toml` is authoritative and its Markdown index is generated.
WordCraft proofing tests need the pinned craft-i18n input as well as the optional font input.
SoundCraft’s reference-video work stays outside its real-time audio callback.
Launcher time uses Jiff under its local rule, rather than adding Chrono beside it.

Audit new edition labels against all ten required languages: en, pl, pt_BR, fr, de, es, ja, ko, zh_CN and zh_TW.
An app advertising a language does not prove a newly added label has a row in its catalog.
Include native file-picker filters, native window titles and dynamic media-layout descriptions in the source-diff audit; a scan of translation macros alone misses those call sites.
A green gate may still report missing translations without failing, so check the actual new labels through the app’s lookup too.
Check the actual lookup and bare-language routing, preserving separate simplified and traditional Chinese catalogs.
Keep upstream catalog identifiers such as `pt-br` or `zh-hant` where their lookup expects them.

## The closure that exposed the gap

PhotoCraft [#7818](https://github.com/storytold/photocraft/pull/7818) was closed on 2026-11-05 with FredApps' requested changes of 2026-10-19 still open: the review clock runs from the review, so answer it, or say when the answer comes.
The maintainer invited a current-main rebase and a reopened or fresh PR.
That historical closure is not today's thirty-day rule.
FredApps corrected his own point 2: PNG normalization remains a maintainer decision; he withdrew the claim that the cited issue promised unchanged stored pixels.
Preserve the correction when answering the review.

The two CodeRabbit findings were truncated MPO entries silently losing damage reporting and Duotone stereo exports bypassing ink rendering.
Confirm each against the submitted head, then cite the fixing commit and a regression, or explain with measured evidence why it no longer applies.

## Authorship and assistance are different claims

Read the exact wording before declaring an attribution-policy conflict.
Craft core rule 15 says a pull request does not say an agent wrote it; acknowledging assistance does not make the assistant its author.
Keep the person as author and accountable reviewer, with no “Generated with” line in the pull request.
Our new commits carry an `Assisted-by:` trailer; acknowledge AI assistance once in the fresh pull request description and do not repeat it in replies.
Do not rewrite a trailer that is already in a commit, ours or anyone's: a commit trailer is not the pull request saying an agent wrote it, and the projects use the other form themselves.
Measured on 2026-11-12 over the last 400 commits of each main branch: LightCraft carried 128 `Co-Authored-By` trailers naming a model, PhotoCraft 78 and FilmCraft 107, maintainers' commits among them, and none carried `Assisted-by`.
LightCraft's About ▸ Models page reads the `Co-Authored-By` trailers (`crates/ui-egui/src/dialogs/credits.rs`, `docs/contributors.md`), so removing one removes a credit the program shows.
Count before proposing a history rewrite: `git log -400 --format='%(trailers:key=Co-Authored-By,valueonly)' origin/main`.
Do not claim a person's review happened before it did: a draft's first-person review assertion must be checked by that person before sending.
A local draft is not authorization to send.

## When a rebased gate disagrees with main

Read a successful gate for the same source commit and compare its measured toolchain and inputs before changing untouched code.
`Cargo.toml`'s `rust-version` is a minimum, not a CI pin.
PhotoCraft's [passing gate at de7e1eec](https://github.com/storytold/photocraft/actions/runs/42861583249/job/129988830503) used Rust 1.99.1 on 2026-11-10, while the local Debian SDK supplied 1.97.1.
The older Clippy complained about unchanged PSD callback and cursor-range code.
Match the actual gate compiler, Clippy, font input and software GPU checks, then repeat the unchanged-source check; do not silence the diagnostic or fold an environment workaround into a media fix.

A login shell can silently select the older compiler even after the SDK was corrected.
In the November LightCraft port, `docker exec ... rustc --version` reported 1.99.1, but the diagnostic's `bash -lc` reset `PATH` and ran Debian's 1.97.1 Cargo, compiler and Clippy.
Comparing `command -v` and versions inside the exact command shell exposed the difference; duplicate Cargo metadata headers independently identified both compilers.
Use a non-login shell that preserves the SDK environment, or explicitly select its pinned tools, and print Cargo, rustc, Clippy and rustfmt versions in that same shell before the gate.
Record the mismatched run separately; it does not establish the required-toolchain result.

Read the environment on the specific CI job too, not only its shell command.
PhotoCraft’s corpus job at de7e1eec runs `cargo xtask test-corpus` with `CARGO_PROFILE_RELEASE_LTO=false` and `CARGO_PROFILE_RELEASE_CODEGEN_UNITS=16`.
The default release profile applies thin LTO separately to many integration-test binaries, which needlessly changed the local build workload.
Match the job’s explicit overrides while retaining its complete package, feature and test selection; record an interrupted mismatched-profile attempt separately from the resulting gate.

## Dependency resolution passes, but the rebased source does not compile

`cargo metadata` checks the dependency graph, not field names, constructor shapes or the receiving app's lint policy.
FilmCraft's November port still used a removed toast field, an unboxed media item in a test and an `egui::ComboBox` forbidden by its newer shared-widget policy.
The compiler diagnostics, current type definitions and existing callers identified these mismatches.
Preserve the live path's newer behavior when removing obsolete helpers; reconnecting an old helper can discard changes made on main.
For several independent compile errors, `cargo clippy --workspace --all-targets --keep-going -- -D warnings` collects the remaining diagnostics together.
This is a diagnostic step, not a replacement gate: run the receiving project's unchanged complete gate before committing or calling the port green.

## Native tests pass, but a rebased tracker fails parity

LightCraft's November port passed its complete native test stage, then failed parity on duplicate import/export row IDs and an export-test path moved on main.
The replay had appended the older stereo rows and header after the current tracker instead of merging their new details into its existing rows.
Keep the current row's content and status, add the feature details and live test references there, remove the appended duplicates, and refresh the generated summary with `cargo xtask parity --write`.
The focused parity check then passed; the receiving full gate remains required before the port is committed.
Run a repository's inexpensive tracker/reference check early alongside compile diagnostics after a large rebase, so documentation errors appear before its long native test stage.

## Save As regression sees no warnings for JPEG

PhotoCraft's layered stereo Save As regression failed on `copy.jpg` after rebasing because its direct `save_as` call stopped at the newer JPEG Options prompt.
The empty warning list described a pending answer, not a completed export.
The `save_to` prompt branch and the already passing edition regression exposed the cause.
Complete the existing UI command with `menus::invoke(..., "file.saveAs", json!({"path": path, "jpegFormat": "baseline"}))` before checking the metadata-loss warning and unchanged editable identity.
Keep those assertions; do not suppress the prompt in production or claim the save completed merely because its initial call succeeded.
Run the focused regression first, then the receiving branch's full gate; another branch's passing result does not certify an omitted test port.

## Rebase succeeds, but two branches assigned the same catalog version

LightCraft's stereo branch and later upstream Lens Blur work both used catalog version 13.
The replay compiled, but a regression requiring an upgrade before appending stereo operations failed: the journal reported no upgrade for version 13.
Read the receiving journal's format history and writer constant together; preserving both history entries does not change the writer.
Assign the newly combined format the next version and update operation/field version checks.
Test both older forms independently: upstream Lens Blur data and the earlier edition's stereo metadata must survive opening, migration, appending and reopening.
The writer-14 correction passed the complete nine-stage gate, including HEIF and wasm; focused catalog tests alone were not the receiving gate.

When restoring that branch from a bundle, distinguish the main revision observed later from the actual ancestor used as a bundle prerequisite.
LightCraft's accepted head shared an older base with the later main; requiring the later main itself to be its ancestor incorrectly rejected a valid checkpoint.
Use the actual merge base for restoration, retain the observed main separately, and verify the bundle and advertised head.
Then reconcile the later source changes explicitly; a valid bundle does not mean they were integrated.

## A shared-library port landed while the app pull request stayed open

Symptom: a maintainer says the HEIF work landed through craft-libs, but the app branch still carries a decoder copy and stereo commits.
Read the merged diff and its explicit exclusions before dropping commits.
In [craft-libs #841](https://github.com/storytold/craft-libs/pull/841), only the synthetic `Spec::stereo` part of Mitch Lindgren's LightCraft import commit was ported; app detection, catalog, badges, filters and views were outside that port.
The primary metadata reader came from a different contributor's pull request.
Map original commits to functions and retained app changes, including partially superseded commits; preserve their authors and check squash co-author trailers rather than calling the original hashes main ancestors.
Use the shared implementation once, and keep any still-missing selected-item API in that owner.
An app's migration to the shared crate can itself still be open; carry it credited and name that dependency instead of describing it as merged.

Symptom: the extracted KRA and ORA crates' existing small-stack regressions abort in the shared workspace while their donor app passed.
Compare build profiles as well as source: PhotoCraft builds its own crates at dev optimisation level 1, while the new shared crate inherited level 0.
The same regressions failed at level 0 and passed at level 1 with their explicit 512 KiB stacks, nesting limits and assertions unchanged.
Narrow package-specific dev profiles restored the donor setting, like the shared workspace's existing Affinity exception.
Record this as a build-profile correction, not a claim to have made the parser nonrecursive or proved every caller's stack size.

A reopen test also failed when a fast injected log-writer failure made a snapshot due inside the command's own persist.
The snapshot retained the changed flag, so the product correctly allowed reopening; the test had not established its intended no-snapshot precondition.
A bounded first-write handshake held the injected failure until the command returned, keeping the original refusal, unsaved-state, data-retention and retry assertions and the separate positive snapshot/reopen test.
A controlled run first forced the observed interleaving and checked that the successful reopen retained the change; the corrected seven-test slow-drive group then passed without changing production persistence code.
Do not replace that synchronization with a longer sleep or remove the refusal assertion.

## Duotone pixels match, but the warning counts a virtual layer

PhotoCraft's stereo ink rendering initially matched ordinary export pixels but reported that two layers were flattened for a single-layer Duotone document.
The RGB preparation adds a temporary ink adjustment, which the flat renderer counts as another layer.
The ordinary Duotone exporter already removes that artificial-layer warning; reuse its policy in the stereo path only when the same preparation was used.
A regression comparing ordinary and stereo warnings failed on MPO before that correction.
Check the ink-to-RGB notice and actual RGB layer-loss notice separately, along with exact PNG colors and the JPEG encoder's bounded color difference.
Do not hide unrelated fidelity warnings or suppress flattening notices for ordinary RGB documents.

After building the complete CI feature graph, use the same workspace, features and test targets with a nextest filter for focused checks when appropriate.
A package-only default-feature invocation can select a different graph and rebuild shared dependencies; it is useful coverage when intentional, and is not a substitute for the full receiving gate.

## Keep the app and shared-library revision together

An app gate on an older library revision proves that binding only.
Record the app revision and every sibling-path library revision with each gate and GUI build.
When a newer shared API breaks an app test, check the app's current main before writing a port.
Dylan M. Taylor's [2bb0273d](https://github.com/storytold/filmcraft/commit/2bb0273d0fea73041f8cbe7d394929ec9d3f7faf) already updates six Matroska oracle constructors for `OpenOptions::index_limit`.
Those constructors use `..OpenOptions::default()` while retaining their indexing and CRC choices.
Carry the upstream change with its credit; a replay at the preceding library revision is not a receiving test for the newer one.

## Separate a launcher failure from a failed gate

If a container exits before the first Cargo line, inspect its state, exit code and logs before removing it.
Reproduce the launch with a trivial payload before changing Rust code or retrying the suite.
A GNU timeout 9.10 run reproduced exit 125 with `true` when timeout was the final shell command.
Keeping the enclosing shell restored the expected statuses: success 0, failure 1 and expiration 124.
The measured fix retains the shell and propagates the payload status:

```sh
gate_status=0
timeout 120m cargo xtask ci || gate_status=$?
exit "$gate_status"
```

Check all three statuses; a wrapper that only proves success can hide a failed test.
This observation does not establish a general Cargo or coreutils defect.

## Establish an audio test's queued lead

A fixed warm-up sleep does not prove that a background mixer published the frames a test will consume.
A channel-mapping test with four 512-frame callbacks needs 2048 frames queued before requiring zero underruns.
Use a bounded readiness signal while retaining every exact sample and underrun assertion.
admbe’s open [FilmCraft #3058](https://github.com/storytold/filmcraft/pull/3058) already uses a published-block wait for this case, through its new `blocks_mixed` statistic.
A backport to the preceding producer API can acknowledge prior publications at the next mixer entry while preserving that API.
Verify publication in the producer's actual order, not merely that a mixing call started or returned.
If the next mixer entry acknowledges preceding ring publications, its Release counter and the test's Acquire load establish that order.
See Rust's [atomic ordering documentation](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html).
A controlled producer delay can distinguish a missing precondition from bad channel mapping.
The old warm-up produces expected silence when the first block drains.
Establishing the lead preserves the exact samples.
Keep the delayed-producer red and green witnesses separately from the ordinary complete gate.

## Measure the optional inputs, not their variable names

AniCraft’s Linux gate calls the shared workflow with a pinned craft-fonts checkout.
Its current build script looks for `Inter-Regular.ttf` and `JetBrainsMono-Regular.ttf`, while the supplied shared checkout may contain neither name.
Record the actual build warnings and generated font payload, and give the untouched stock control the same input and fallback.
A set `CRAFT_FONTS_REQUIRED=1` does not prove an app implements that requirement or embedded the intended faces.
Do not copy unrelated font files into another project’s sources to hide the warning.

Check the receiving app’s exact gate before imposing a suite-wide formatter command.
A newer formatter can rewrite untouched owner files even when the app’s actual gate is tests and strict Clippy.
Inspect the diff before committing, restore unrelated formatting churn, and rerun the semantic checks on the isolated change.
Keep a mutating formatter run separate from an unchanged-source gate receipt.

## Read the current review clock

A historical two-week closure, such as PhotoCraft #7818, is evidence about that review, not a timeless suite-wide deadline.
The current core rule 14 at `dde09ea31e2e457f5b4653a6e76f7cdf55944bdf` requires an answer to actionable author feedback in seven days, a reminder at fourteen and eligibility for a maintainer-decided closure at thirty.
Suggestions and unconfirmed bot findings do not start that clock; waiting on a maintainer pauses it, and an actual fix, explanation or agreed plan resets it.
Read the receiving repository’s stamped rule before describing its current practice; retain the original dates when recounting an older lapse.

## A new whole-workspace gate can expose an existing upstream failure

Symptom: the current craft-libs workspace test process aborts in `craft-kra`'s 512 KiB nested-document test before reaching a new camera crate.
Search the failing path's default-branch commits, open and merged pull requests, and issues before changing a stack limit or writing another parser fix.
Dylan M. Taylor's [PR #1126](https://github.com/storytold/craft-libs/pull/1126) already supplies an explicit layer stack and its lint follow-up.
A file-scoped port can retain his authorship, original author date and both source commit references while keeping unrelated rendering changes out of a stereo subject.
Keep the failing whole gate and the passing reader regression, then rerun the whole gate.
An existing upstream fix needs credit and a receiving test, not a duplicate contribution.


### Whole-library features need their declared test inputs

Symptom: a whole `craft-libs` all-features run fails every keymap dialog and the PSD corpus tests, although the default workspace passed.
Cause: the dialog suite requires the pinned `craft-fonts` checkout named in its own workflow, and PSD's opt-in `corpus` feature deliberately fails without the PhotoCraft PSD and ATN corpus.
Fix: supply `CRAFT_FONTS_DIR` at the workflow's exact revision and `CRAFT_PSD_CORPUS` at the verified PhotoCraft corpus root; keep every assertion enabled.
Found by reading the failure messages, `keymap.yml`, `tests/support/fonts.rs` and PSD's `corpus_dir` implementation.
A missing input is not evidence of a new camera defect, and a selected-test pass is not a whole-workspace pass.

### Control methods and engine commands are different surfaces

Symptom: a TextureCraft engine regression stops at `UnknownCommand("session.inspect")`, before reaching the intended stereo assertion.
Cause: `session.inspect` is a desktop control-channel method; the engine registers `project.inspect` and exposes `inspect::session` directly.
Fix: use the registered engine command or the direct inspector in engine tests, keeping the control-channel spelling in desktop RPC clients.
How found: reading the command registry and control protocol after the failed test.
Also read the current project limits before making a fixture: the inspected project minimum was 128 texture pixels, so a 64-pixel project failed before the feature test.
That is independent of a 64×64 upload tile and the chosen per-eye render dimensions.
Keep those failed fixture attempts as diagnostics, then rerun the intended semantic red before implementing the feature.

Symptom: regenerating a lockfile offline rejects an already locked yanked transitive version.
Cause: `cargo generate-lockfile` resolves the entire graph again; it is not the minimal operation for adding one local shared crate.
Keep the existing lockfile and let an ordinary offline check add the new path dependency, then verify that existing package versions are retained and use `--locked` for acceptance gates.
The observed check added six window dependencies and removed no existing package versions.
A bare egui UI-library check can also lack a native window-system feature; use that project's actual app, all-targets gate or test targets, which supply the platform features, rather than adding a host-specific feature to production manifests.

### Stock and edition worktrees in one Cargo target

Symptom: a release rebuild says `no field stereo on type Session` although the checked edition source defines it and its complete development gate passes.
Cause: a shared target still contains release artifacts from the preceding stock workspace with the same package names; the dependency metadata uses relative workspace paths.
How found: the release build reused the engine instead of compiling it, then failed in the changed UI; resetting every workspace package's release artifacts made the same unchanged source rebuild successfully.
Use `cargo metadata --no-deps --format-version 1 --locked --offline` to identify `workspace_members`, then pass every corresponding package name to `cargo clean --release` with repeated `-p` arguments before switching between those trees.
Keep third-party dependencies only when their source inputs are unchanged; the app's workspace artifacts must be rebuilt from the intended tree.
A full `cargo clean` also resets the target and is the normal boundary between completed apps.
For a baseline comparison, reset before building stock too, retain both compilation logs and use the identical temporary whole-UI test on each side.
A runtime command-registry and session-inspection check can confirm that the candidate has the added API and pristine stock does not.
Source cleanliness and a source hash alone do not prove which cached library was linked.

### Local path libraries and frozen gate inputs

Symptom: the full app gate reports that a renderer depends on an app or tooling when its new sibling dependency is a shared camera library.
Cause: the local layer checker classifies every dependency with a path as a workspace member, although Cargo metadata distinguishes actual `workspace_members`.
Fix: classify app workspace crates from the member set; keep the existing upward-layer and UI-toolkit prohibitions.
How found: the complete MaterialCraft gate reached its layer stage and failed on `craft-stereo-camera`; the metadata regression failed before the one-line classifier change and all sixteen checker tests passed afterwards.
The same fix already existed in the edition's TextureCraft branch, so check other accepted suite work as well as upstream before recreating a fix.
A sibling path does not make a shared library part of the app workspace.

Symptom: test commands pass, but the gate receipt refuses to bind them to the final source tree.
Cause: a formatter was still changing a new test when the source guard recorded its inputs.
Fix: wait for formatting and intentional lockfile resolution to finish before freezing source and harness hashes, then run the gate without source mutations.
How found: the before/after receipt isolated the changed stock-control test hash; a fresh run on fixed sources passed both the checks and the unchanged-source guard.
Keep the refused receipt as diagnostic evidence and use only the fixed-source run for acceptance.

### A moving stable compiler and carried prerequisites

When a workflow says `stable`, read the current signed Rust channel manifest before choosing the SDK; record the actual compiler version beside the gate result.
A previously accepted image can cease to represent that workflow overnight.
For standalone toolchains, verify the official signing certificate's pinned fingerprint, the manifest signature and each component hash before running an installer.

Symptom: the same workspace passes its previous compiler but fails strict Clippy on the next stable compiler.
Cause: the gate followed `stable` while the private SDK retained an older release.
Fix: use the workflow's current compiler, search the affected upstream file and carry an existing baseline fix with its author's identity and date.
How found: the official channel changed from Rust 1.99.1 to 1.100.0; the new Clippy diagnostic named `craft-cms::synth`, and upstream already had Dylan M. Taylor's baseline fix.
Do not change an unrelated application's dependency pins merely because a library's workspace lint failed.

Symptom: carrying an upstream baseline fix makes a plotter golden test expect `TB54,0,0`, but the branch's command encoder omits it.
Cause: that fix assumed an earlier functional prerequisite from upstream main.
Fix: carry the prerequisite with its author, rather than weakening the golden output back to the old encoder.
How found: the failing expected command sequence, the upstream file log and the prerequisite's source diff; all 14 plotter goldens then passed.
This is a byte-stream test, not a claim of testing a physical cutter.

Symptom: an exact-carry audit rejects a correctly applied cherry-pick.
Cause: raw Git diffs also contain blob hashes and hunk line numbers, and some files in the original commit may already be present from an earlier carry.
Fix: compare author/date, the resulting affected file bytes where appropriate, and every changed hunk byte while excluding only Git's index hashes and hunk locations.
Preserve whitespace; a stable patch-id alone is insufficient for a byte-for-byte claim.
How found: the two already-carried KRA/ORA files matched upstream exactly, while the root Cargo manifest retained the branch's own stereo dependencies outside the imported hunk.

Symptom: the whole gate passes tests, WASM and licenses, then cargo-deny fails resolving the RustSec database host in an isolated container.
Cause: Cargo's `CARGO_NET_OFFLINE` does not set cargo-deny's separate global offline flag; its default check still fetches the advisory database.
Fix: fetch public check data in a separate preparation step, then use `cargo deny --offline --log-level error check` in the isolated check environment.
Keep advisory, bans, license and source checks enabled; offline mode still enforces the configured maximum database age.
If the project's xtask hardcodes the command, keep its workflow and source unchanged and record any transparent tool wrapper as an explicit transport adjustment, including the database revision and real tool version.
How found: the failed command named the absent RustSec clone; cargo-deny 0.20.2's global help and `check.rs` distinguish `Fetch::Disallow(maximum_db_staleness)` from its online fetch mode.
The separately fetched database made all four offline checks pass; an empty database must remain a failure rather than a successful skip.

Symptom: the whole app suite passes its new feature tests but fails `the_flatpak_manifests_pin_the_craft_i18n_rev`.
Cause: the native catalog input was advanced while the two existing Flatpak source pins retained the old revision.
Fix: update every existing catalog-pin consumer in the same feature change, retaining the equality regression and the upstream packaging design.
How found: nextest named the one failed test; its definition reads both manifests and compares their source commits with `craft-i18n.rev`.
This source consistency check does not establish that an unpublished catalog commit can already be fetched by a package builder; record local-only inputs and do not claim a Flatpak build.

Symptom: `cargo xtask assets` succeeds but the whole CI fails `license-check` with `NOTICE: document hash mismatch`.
Cause: the generated asset attribution and the audited source-document map are independent checks; adding a required copyright notice changes the latter input too.
Fix: reread the relevant original license and notice, verify the font or asset digest, then update only the matching `LICENSES.toml` checksum and rerun the complete gate.
How found: the full gate reached the source-document validator after all workspace tests and WASM checks passed; its exact diagnostic identified the stale document mapping.
Do not refresh every hash automatically or remove the integrity guard.

Symptom: the full CI passes required language and glyph checks, but the built GUI refuses Korean with `language must be one of auto, en`.
Cause: the CI helper exports catalog and font inputs in a child shell; a later `cargo build` in its parent does not inherit those exports and produces the optional-input executable.
Fix: put required-input exports around the entire gate and executable build, or explicitly wrap each command with the same environment helper.
How found: a real native `ui.set language=ko` probe rejected the archived executable even though CI's required-input test body had run.
Rebuild and repeat the native captures on the corrected executable; preserve the first binary and failed probe as diagnostics.
Add a runtime non-English-language request to every capture so this build-input error cannot pass an English geometry proof again.

Symptom: `git bundle verify` reports a complete history, but fetching it into a fresh bare repository fails to read a parent at an old shallow boundary.
Cause: the source repository still records a shallow boundary from an earlier checkpoint; the bundle does not contain a traversable full ancestor graph.
Fix: inspect `git rev-parse --is-shallow-repository`, restore ancestors from the validated public source with `git fetch --unshallow`, and compare every existing local branch head before and after.
Then recreate the bundle and actually fetch it into a new database, compare its advertised heads and trees, and run `git fsck --full`.
How found: the first fresh catalog restore reported the missing parent even though bundle verification had succeeded; the source's shallow flag confirmed the cause.
If complete ancestors cannot be obtained, state the exact prerequisite or shallow boundary and do not claim full history.
Never rewrite an author, parent or date to make a checkpoint appear complete.

Symptom: a Python archive restore check rejects a source file although its extracted SHA-256 matches.
Cause: `tarfile`'s secure `data` filter intentionally strips group-write permission, so a stored 0664 source file is extracted as 0644.
Fix: retain original source modes in the manifest and write explicit safe 0644 or 0755 source-archive headers, while checking tested executable bytes and modes exactly.
How found: compare source, stored member and extracted modes beside their matching hashes before changing the check.
Keep the secure extraction filter; do not disable it to preserve an incidental group-write bit.
