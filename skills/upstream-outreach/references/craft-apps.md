# Craft Apps: contributions and review follow-through

## Converge the actual dependency graph

When a suite needs one shared-library revision, inspect every tracked Cargo manifest, including the web frontends and root patches.
Record each consumer's old sources before changing an edition branch; keep a clean offer branch separate.
After binding the new revision, inspect resolved package manifests and sources as well as the lockfile.
Every package owned by craft-libs must come from the selected checkout or revision, including UI helpers, updater, codecs and vendored reader patches.
Run each receiving app's complete gate and repeat proofs for the shared paths that changed.

Source-audit trap: the stereo crate uses the new checkout, while the app still resolves helpers and web crates from several older craft-libs revisions.
Cause: changing the visible stereo dependency does not change unrelated workspace entries or child manifests.
Fix: converge the whole resolved graph and retain a before/after source inventory; a successful metadata command still does not establish compilation or native output.
How found: an inventory of seven apps' root and web manifests showed local stereo crates beside independently pinned UI, updater, image and web helpers.

Source-audit trap: a catalog revision file is present, but the executable still embeds its local translations.
Cause: a revision file does not create a build-script input; pre-cutover apps can ignore CRAFT_I18N_DIR entirely.
Fix: inspect the actual build and lookup paths, carry an existing upstream migration with its authorship when available, and verify required-input and ordinary-output controls before claiming a common catalog.
How found: source inspection found three local-catalog consumers alongside four apps that already read the shared input.
Do not describe an unused catalog pin as convergence or silently discard untranslated local rows during migration.

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

## A shared dependency fails a receiving app’s source guard

Symptom: the shared library’s Linux gate passes, but an app refuses its lockfile because a transitive Windows-only Git dependency points outside Storytold.
Cause: the shared library carries an open contributor fix through its author’s fork, while the receiving app deliberately restricts Git sources.
Fix: retain the needed fix and its original author/date; use a documented permissive source snapshot in the shared owner when that fits the project’s rules.
Keep the real source URL, revision, licence, original hashes and exact carried patch; never relabel a fork URL, add a hidden Cargo source replacement or weaken the receiving workflow.
Then resolve the complete graph and rerun the unchanged receiving guard and gate.
How found: PhotoCraft’s actual workflow check named the inherited winprint fork, and the shared print manifest named the pending driver-options fix it required.
A Linux pass does not prove Windows printing.

Symptom: vendoring a source package also imports document fixtures with embedded fonts of unestablished redistribution terms.
Cause: a package’s source licence does not establish every embedded asset’s terms.
Fix: preserve required source notices and replace those binary fixtures with original, attributed font-free patterns, with a sidecar and hash for every file.
Keep the original test sources; compare the independently rasterized representations and state which platform renderer was not run.
How found: the original print-test PDF’s FontFile2 objects named DengXian and MS-Gothic; the replacement PDFs listed zero fonts and rasterized exactly to their matching TIFFs.

Symptom: `cargo fmt --all --check` rewrites vendored source under the containing workspace’s formatting choices.
Cause: path dependencies are included in that check and can inherit the parent formatting file.
Fix: preserve the dependency’s own formatting configuration and record any minimal formatting-only import adjustments separately from the credited upstream patch.
Never call a modified full snapshot byte-identical; verify the carried fix’s affected file or changed hunk bytes independently.
How found: the imported print wrapper had two layout-only differences under default rustfmt; its carried PrintTicket file still matched upstream exactly.

## Complete catalog branches and format-pin prerequisites

Symptom: an all-branches log shows accepted translations, but the selected catalog tree has no app files for them.
Cause: the candidate was based on one app’s catalog topic; other accepted topics existed as refs without being merged into that tree.
Fix: check each topic with `git merge-base --is-ancestor <accepted-topic> HEAD`, inspect `git ls-tree -r --name-only HEAD -- locales`, and verify the files the receiving app actually reads.
Compose the topic histories, retain every attribution block, then run the data repository’s complete gate and the apps’ required-input checks.
How found: the source audit found zero AniCraft and MaterialCraft catalogs in the candidate, despite their commits appearing in `git log --all`; merging their accepted history restored their exact file bytes.
A matching revision file or an existing Git object does not establish catalog consumption.

Symptom: a required catalog cutover cannot provide languages already offered by the app, or loses many existing translations.
Cause: the shared checkout predates the app’s latest in-repository catalogs.
Fix: read its recorded sync base in ATTRIBUTION.md and use the official `tools/sync_app.py` delta migration against the accepted app head.
Preserve untouched shared corrections, check the round trip, credit the real source and rerun the data gate; do not silently embed English instead.
How found: FilmCraft’s check reported four missing registered app catalogs and 20,136 missing or different rows; its delta migration reproduced all 55,697 eligible source rows without changing common.tsv.
Prefetch the historical source blobs before running the migration offline; a partial clone can know a commit without holding its catalog contents.

Symptom: a shared format upgrade makes the old app test fail with a corrupt-file error naming `full_composite`.
Cause: the app’s last format pin skipped that optional member, while the new shared envelope deliberately validates it like the thumbnail and composite paths.
Fix: read the shared format contract and search upstream before adding another parser API or relaxing its guard.
[PhotoCraft #13092](https://github.com/storytold/photocraft/pull/13092), by dotCooCoo, contains the exact pin-transition regression: a malformed path must return Corrupt naming the field, while a bundle without the optional member still opens.
How found: the full receiving gate named the old assertion, and the PR’s original non-merge commit fb7368e5d explained the same transition.
Carry the original author and date; when the edition’s common-source binding supersedes the PR’s Git pin and lock lines, identify that scope and verify the applicable test hunk instead of claiming whole-commit byte identity.

Symptom: importing a local bundle prerequisite fails with `lazy fetching disabled` and `could not fetch ... from promisor remote`, although the source is not shallow.
Cause: a partial clone knows the commit but lacks promised historical objects; upload-pack disables lazy fetching while serving that clone.
Fix: fetch the exact accepted prerequisite from the verified public repository into the empty restore database, then import the incremental bundle and compare its head and tree before full fsck.
Keep the prerequisite explicit; do not call an incremental bundle standalone or rewrite the source history to repair a transfer.
How found: the shallow check returned false, the local transfer named the promisor restriction, and the public prerequisite allowed all four checkpoint head/tree restores and all three working-patch restores to pass.
Untracked source files need their own saved bytes and hashes; a committed head restore alone does not preserve receiving work in progress.

## A common revision must retain every accepted subject

Symptom: the common library passes its whole gate, but the first receiving app fails because `VideoParams.stereo_mode` is missing.
Cause: the candidate composed current main and a recent camera branch without merging the accepted media branch; its own missing tests could not detect those omitted APIs.
Fix: audit the ancestry and actual source of every previously received library revision, then compose the complete accepted subjects before qualifying consumers.
Retain the newer window, protocol and camera paths while restoring container metadata, native sample grids and selected-item decoding in their shared owners.
How found: FilmCraft's real receiving compile named the missing field; comparing its accepted library tree also found the stereo grid module and selected HEIF API absent.
A successful library gate establishes the selected source's checks, not that the candidate contains every earlier edition feature.

Symptom: a source-owner check passes even when a resolved shared crate points to an older sibling checkout.
Cause: it rejected old Git sources and checked selected PDF backends, but did not compare every shared package's resolved manifest with its canonical owner.
Fix: map package names from the selected library's crate and vendor manifests to their canonical manifest paths, then compare the complete locked Cargo metadata graph, including helpers and web dependencies.
Keep build-input revision checks too; a matching revision file does not establish which source Cargo compiled.
How found: changing only the resolved stereo-window manifest path in a saved graph made the old checker return success; the complete-owner checker rejected that control and accepted the unchanged actual graph.
The same complete check later caught PdfCraft's Windows-only `winprint` edge still on Git after its shared root dependencies had converged.
Bind direct target-specific dependencies to the selected owner too; a successful Linux metadata check establishes their source identity, not Windows runtime behavior.
Run the receiving app's own full gate and bind its executable and fresh proofs to that same owner; a metadata check alone is not compilation or runtime evidence.

Symptom: `windows_default_leaves_out_gl` fails at its assertion about eframe's default before testing the app's Windows policy.
Cause: the private runner forced `WGPU_BACKEND=vulkan`; eframe's `WgpuSetupCreateNew` reads `Backends::from_env()` before its `PRIMARY | GL` default.
Fix: preserve the app assertion and remove that override from the full-CI child, matching upstream's environment.
Keep the software Vulkan ICD selected; explicit backend requirements belong in the targeted GPU checks rather than a suite that tests unmodified defaults.
How found: the complete FilmCraft run passed 5,076 tests and failed that one precondition; the same unchanged test passed after removing only `WGPU_BACKEND`.
Rerun the whole gate after the controlled check; a one-test pass does not establish full CI success.

The corrected full Linux gate then passed all 5,077 native tests and eight doctests, plus its layer, asset and WebAssembly checks, with production and test source unchanged.

Symptom: LightCraft's `tiles_sharing_one_payload_count_its_bytes_once` expects the distinct-byte refusal but receives `264 image data chunks, expected 65536` after a shared TIFF update.
Cause: `ImageInfo::chunks` bounds allocated descriptors by file length; its returned length is no longer the declared offsets count.
The fixture still declares all 65,536 offsets pointing to one 256-byte payload.
Fix: carry the existing upstream RAW comparison of `info.offsets.len()` against the required grid count, preserving the later distinct-byte plausibility check and the unchanged regression.
[LightCraft #4165](https://github.com/storytold/lightcraft/pull/4165), by Dylan M. Taylor, includes that exact hunk in e4dd081d; shared [craft-libs #1102](https://github.com/storytold/craft-libs/pull/1102) explains the same transition after the RAW migration.
Identify the applicable hunk and retain its author's date rather than importing unrelated gain-map and HEIF changes or padding the fixture to evade the descriptor cap.
How found: the full receiving gate reached the unchanged RAW regression, inspection separated declared offsets from bounded descriptors, and the upstream search named the existing fix.
All ten related tile tests passed with that original hunk and no assertion change; the whole receiving gate must also pass before closing the dependency step.

Symptom: EffectCraft’s existing script-fallback regression reports the same family on both sides, yet the chosen face changes after earlier lookups.
Print the face IDs and styles as well as the family before changing the environment or the assertion.
The measured Hebrew lookup changed from Liberation Mono Regular to Bold after other searches loaded the bold face.
Cause: the loaded-face path returned that face directly, while the exhaustive path resolved its family in the requested style.
Fix: apply the same requested-style resolution to the loaded covering family, retaining the covering face when the resolved style lacks the character.
How found: the unchanged assertion failed with the extra diagnostics, the two selection paths differed at the return, and the same focused regression passed after the correction with the font inputs unchanged.
This establishes the measured style correction; unrelated fallback-family ordering and unavailable writing systems need their own controls.

## A receiver has newer APIs than its common backend

Compare the receiver's real compile errors with the shared owner's public definitions before moving pins.
Find each missing behavior's original upstream commit and its prerequisites.
Port it into the common owner while retaining that owner's independent decoder bounds, cancellation and work limits.
Keep original authors and dates on directly carried vendor subjects; identify partial ports rather than claiming whole-commit identity.
Run the standalone backend contract job, the common library gate and every receiver's complete gate before calling a new suite revision green.
A passing backend job alone does not establish receiver compatibility.

Symptom: a PDF receiver names missing viewer-state, repaired-update and page-work APIs after its dependencies converge on one common checkout.
Cause: the common snapshot and the receiver evolved independently; a broad three-way merge also includes rendering and hostile-input changes on both sides.
Fix: reconcile the actual behavior in the common owner, including warning propagation and every budget consumer, before moving the suite's common pin.
Keep the receiver's private backend out of the resolved graph.
How found: the real PdfCraft compile named fifteen missing API uses; a subsequent backend compile found a cancellation regression still treating a new `(XRef, bool)` result as an `XRef`.
The tuple consumer was updated without changing its cancellation assertion, and the standalone backend job passed1190 tests.
Three identical raster regressions compiled against the pre-merge head and failed their pixel assertions, then passed on the reconciled source.
The first complete library gate stopped at its disk floor after both strict Clippy configurations passed.
Its source was kept as a hashed working patch; the stopped job was not relabeled green when space recovered.
After explicit resumption, the same frozen source completed both native configurations, WebAssembly, release camera tests, the minimum-Rust check and standalone backends: 23,705 passed, zero failed and 113 ignored across 942 result groups.
The standalone subset passed 1,193 tests, including the new marker/cancellation control in its feature variants.
That qualifies the shared code tree, not the receiving apps; keep the last qualified edition pins until each receiving gate and its diagnostic mapping are checked.

Symptom: a transferred source manifest's historical SHA-256 disagrees with the named revision, while its recorded Git blob agrees.
Cause: the historical source-hash field is wrong; it is distinct from the local patched-file hash.
Fix: fetch the exact named upstream path, verify both its Git blob and SHA-256, then correct only the wrong provenance field.
How found: PdfCraft's `ec0a965074f376a5bf610435948e4e5184bf3299` JPX source hashes to `f0a2b01c692c086d30a26562d7548f9e837af166be737d2c543de7c886a45f82` and Git blob `74efd8b31e2b2935ff2bbceda2c1ffd36ea9c20d`; its separate local patched hash was already correct.
Retain the fetched authority bytes and the before/after comparison.

Symptom: an origin audit reports newly carried files missing from the crate's named base revision.
Cause: the audit ignores a file's more specific source revision.
Fix: resolve the per-file origin before the crate default, then compare both the original Git blob and its SHA-256; keep the local patched hash separate.
How found: the two CMYK modules were absent from the crate base but present at their recorded individual revisions; all 272 Git-origin records then matched without changing a source manifest.

Symptom: a source inventory takes far longer and transfers more data than its selected paths suggest.
Cause: a broad `git grep` over a partial clone hydrates promised blobs outside the intended code read.
Fix: list paths from tree metadata, select the actual owner files, and fetch those bounded files at the recorded commit.
How found: the broad read was interrupted; explicit pinned raw-file reads completed the twelve-app inventory without a repository-wide content search.

Symptom: a new repair regression calls a bounded decode successful and therefore assumes the document limit was bypassed.
Cause: RunLength deliberately returns its bounded prefix, rather than an error, at the limit.
Fix: assert the actual lower byte bound and retain an ordinary full-length control; do not change the decoder policy to satisfy an assumed error result.
How found: the first test received a successful decode, and reading RunLength showed that success can mean a bounded prefix.
The first disk-stopped gate never reached the corrected assertion.
The resumed complete native gate measured 16 bytes under the lower limit and 128 in the ordinary control for both linked and repaired/unlinked updates.
Record the successful runtime assertions against the exact source tree; the earlier source reading only justified correcting the oracle.

Symptom: a receiver's strict Clippy rejects a formerly ordinary `RenderSettings` initializer, while the common owner's own complete gate passed.
Cause: the receiver retained newer raster APIs and Vello 0.0.8 root patches; the common graph also legitimately used the registry's Vello 0.2 ABI through another engine.
Fix: reconcile matching versions in the common owner and propagate its matching patches at the receiving root, where Cargo applies patches.
Validate package name, version and resolved source together; permit a separate registry ABI only when the common lock declares that exact version/source.
How found: PdfCraft first named `max_coverage`; the resolved graph then exposed the two Vello versions.
Controls rejected a private 0.0.8 source, a private 0.2 source, an alternate shared API version and the old Git owner.
The positive common graph retained its intentional registry ABI.
A source-only API inventory also missed renderer and cache prerequisites, so follow each carried subject's actual preimage and tests.

Symptom: the second render of a glyph procedure cut to 64 bytes no longer reports truncation.
Cause: upstream's reviewed Type 3 cache checked the page's remaining content budget, while the shared parser additionally imposed a smaller document-local stream limit.
The cached prefix bypassed that decoder and its warning on the next render.
Fix: retain the original held-content and cache-overhead accounting from PdfCraft's `427c942aad3656dd3e01988f88d88a1c3bed4044`, and qualify caching against the stricter of page and filtered-stream limits.
How found: the same synthetic compressed procedure drew its complete leading path in both renders, but the second render failed the warning assertion before that adaptation.
Both renders then decoded and warned; the original 64 KiB, 32 MiB and font-identity cache controls passed too.
A successful decoder result can be a bounded prefix; a cache must preserve that distinction.

Symptom: a carried helper fails compilation as a duplicate definition.
Cause: the receiver added a CMYK conversion helper where the shared owner already had one, with checked buffer-length arithmetic.
Fix: use the existing shared conversion and preserve its bounds, rather than copying a second implementation into the receiver or deleting the checked one.
How found: the duplicate-definition error led to comparing both bodies; the original isolated-CMYK colour control and existing separation controls passed after the shared helper was reused.

Symptom: five draws of one damaged picture attempt six decodes including the ordinary control picture.
Cause: an empty cache entry meant both a failed decode and a cache miss.
Fix: carry the original bounded failure-cache entry and replay its warnings at every draw; do not cache a page-work refusal as a permanent image failure.
Retain every warning variant the shared owner already exposes.
How found: the original JPX and JBIG2-stencil controls measured six decodes before and two after PdfCraft's `558ffd7f8a65708e292a558625a907cce8dd3e30`, while every failed draw still reported its failure.
The ordinary picture decoded once and drew every time.

### Image refusal metadata and independent decode budgets

Symptom: a refused JBIG2 opacity mask leaves its picture visible in the RGB or plate raster, or still hands the picture to a raw-ink consumer.
Cause: the shared owner's independent dimension and output clamps returned without the stream-refusal marker that the newer receiver uses; the raw-ink path only watched page work exhaustion.
Fix: retain those bounds, mark their refusals, and use one warning/refusal watcher for the picture's RGB and ink consumers.
How found: a synthetic 64 by 16 mask declared as 1 by 1 exceeded the image's size-derived budget; RGB and plate controls exposed the black picture instead of leaving the page white, and the raw-ink control counted one image callback instead of zero.
After the fix, the picture stays hidden, the typed content-limit diagnostic remains visible, and the valid image still reaches the ink consumer once.
Carry the original per-stream metadata subject with its author, preserving the common owner's cancellation and allocation checks.

Symptom: a proposed document-stream-limit test expects a valid known-size image to fail, but the decoder draws it without a warning.
Cause: the oracle conflates ordinary stream materialization with a separate, format-derived known-image budget.
Fix: read the budget definition before changing policy; keep the valid ordinary-cap case as a positive control and exceed the actual declared-image bound in the refusal control.
How found: `filter::decode_limit` derives the known-image allowance from declared dimensions, while `max_decoded_stream` governs ordinary materialization.
The initial 64-byte refusal expectation was wrong and was superseded explicitly; no production limit was relaxed or tightened to satisfy it.

### Receiver behavior needs the reviewed prerequisites too

Symptom: all newly requested public names exist, but the receiver's rendered controls still fail on a wide CMYK group, a nested knockout or a preceding pattern.
Cause: an API-name audit does not identify earlier behavioral review fixes in the receiving backend's history.
Fix: carry the original wide-tile and nested-space, knockout-erase and paint-transform subjects independently, preserving authors and dates and the shared plate/ink paths.
How found: the original multi-scale and nested-space controls lost Difference blending, the knockout control measured different RGB values, and the pattern control measured magenta where the unshifted group was cyan.
The corresponding upstream tests pass after their original fixes; the 256-level black sweep was already green on the imported Vello source and is not a newly reproduced defect.
An RGB fill gains profile-derived CMYK tints in the later receiver, so its older no-tints control must follow that same original commit's RGB-image fixture.
Keep the full library and every receiving application's whole gate as the qualification boundary; component controls alone do not qualify the suite revision.

### Receiving a shared print API without changing printer choices

Symptom: a receiving app fails with `missing field driver_settings in initializer of Job` after moving to the qualified shared library.
Cause: the shared print job gained an optional Windows driver-dialog result, and two app constructors still used the older shape.
Fix: search the app's current main and carry Dylan M. Taylor's original two `driver_settings: None` initializers, retaining his author and date and verifying both complete source postimages.
How found: the whole PdfCraft gate stopped in compilation, the public file history identified the existing fix, and the common `Job` definition explicitly says CUPS ignores that Windows-only field.
The original patch clears strict Clippy on the receiving revision; the complete receiving gate remains a separate qualification step.
Do not remove the shared field, invent a Linux printer setting or describe the compiler error as a reproduced runtime printing failure.

### Clear completed test artifacts at a verified phase boundary

A single Cargo target can still fill the shared build disk when a whole library gate keeps default and all-feature native test executables before WASM, release and MSRV checks.
Keep the disk guard active.
After both native test commands complete, use the actual active Cargo command to verify a subsequent library-check or release-only phase.
Inventory only executed native test paths from that run's log, verify that they are regular executable ELFs inside the owned debug target, and record their sizes and SHA-256 values before removing them.
Refuse a changed or unknown phase before deleting anything; leave source, fixtures, production ELFs, build scripts and active compiler inputs alone.
A guarded run removed 643 completed native test executables and recovered about 6.76 GB while the remaining common gate continued successfully.
How found: the build disk approached its stop threshold, and the actual command transition established which test outputs were finished; the first cleanup attempt refused when the phase changed during hashing.
The full gate still has to finish with unchanged source and harness, and its remaining target is removed after that app is finished.

### A complete API surface can still receive older behavior

Symptom: the shared library's whole gate and the receiver's strict compilation pass, yet the complete receiver suite fails on encrypted streams, annotation geometry and a cached color-space chain.
Cause: checking public names and source ownership establishes neither the older behavioral patches nor the cache invariants the receiver relies on.
Fix: use the receiver's unchanged behavioral failures as the red controls, trace each control to its original upstream subject, and carry that subject into the shared owner with its author's credit.
Preserve shared decoder, allocation, cancellation and work limits rather than selecting the app's private backend again.
How found: the complete PdfCraft run reached every workspace test and exposed failures that the public-name audit and the library's own tests did not cover.
Test-introduction history narrows the search; read the production change and its prerequisites before treating that history as a diagnosis.
The library and every receiver still need their complete gates again on the resulting common revision.

Symptom: a page that selects an ICC alternate chain in reverse order overflows the stack despite a color-space depth limit.
Cause: the profile cache retained its depth-dependent alternate fallback, allowing individually shallow reads to construct a much deeper cached graph.
Fix: retain only the profile's own parse result and resolve its alternate at the depth where it is used, as in Grzegorz Martens's [original fix](https://github.com/storytold/pdfcraft/commit/4c815786c699f3ce745d2dc0a5cb0681fe0d2d76).
Keep the shared owner's existing depth limit; a different limit in the old receiving backend is not authority to raise it.
How found: the unchanged 20,000-link receiver control aborted before the port and completed normally afterwards; the code review located the fallback inside the cached closure.
Also test the other direction, where a profile first encountered at the limit must still read its alternate when selected nearer the top.

Symptom: a shared reference-alias port compiles its main path but fails in a common-only repaired-object branch.
Cause: the new fetch result distinguishes a stored value from another reference, while that recovery branch still returns the old value type.
Fix: preserve the recovery branch and wrap its value, keep repaired-generation matching, and use the reader trait the helper actually requires when reading a reference body.
Keep bounded alias iteration, cancellation and the shared object-stream index cache; read the index dictionary without recursively parsing a stream's Length.
How found: compilation named the unwrapped recovery return and then the helper's overly narrow ObjectLike bound; the Reader definition required only Readable.
The complete Decode-array, Pattern-color and direct reference-alias controls passed after those integration corrections.


### Sampling reviews have an ordered middle prerequisite

Symptom: the original scan-shrink and enlargement controls pass, but a nearly one-to-one scan blurs; adding the sharpness review then breaks a smaller interpolated soft mask.
Cause: the sampling family has three ordered subjects, not just the first change and its final review.
Fix: carry kronbii's [area-average sampling](https://github.com/storytold/pdfcraft/commit/ff227b770ca6e436ee0853a2585739a8be9eb1e9), [interpolated-mask prerequisite](https://github.com/storytold/pdfcraft/commit/5ed2f4ba4f34d5eff689727d468186bc18b53350) and [bounded-row and sharpness review](https://github.com/storytold/pdfcraft/commit/c5065554a1946e4ca8895048d70095f68a4ecec5), in that order.
Retain bounded row intermediates and the common decoder's independent allocation limits.
How found: the unchanged controls first measured 580 blurred pixels near the source resolution, then an abrupt 0-to-255 mask edge where interpolation was expected.
With the complete family, 23 shrink, enlargement, scan, minification and half-pixel controls pass.
Keep every source origin and original date when committing a reviewed same-author family together; a focused green does not qualify the final shared revision.

Symptom: a page-box port passes eleven area controls but loses text placed inside a usable inherited box beyond US Letter.
Cause: filtering an unusable page-owned box after choosing it also discards the opportunity to use the nearest inherited box; the initial subject lacks its later review.
Fix: carry the original page-box recovery and its inherited-box and diagnostic reviews, while retaining the shared owner's US Letter default.
Filter the page-owned box and the nearest inherited box separately; do not search farther past an invalid nearest ancestor.
How found: the original text/raster control expected a 1200 by 1200 page with ink, but received a blank 612 by 792 page; the independent nearest-invalid-ancestor control already passed.
All twelve area controls pass with the reviewed family, including both inheritance cases.
A merge conflict that differs only by A4 versus the already-established Letter default keeps Letter; do not revert that default while carrying the repair.


### A moved catalog can expose old UI test assumptions

Symptom: a French hotbar test cannot find its button, a German prompt test expects a differently worded warning, and a primary-font test rejects a source-shared menu-path symbol after a catalog refresh.
Cause: the tests still assume rows absent from their earlier catalog pin; the application already translates those controls.
Fix: search the current app history again before writing a local substitute.
FredApps's [original three-test correction](https://github.com/storytold/pdfcraft/commit/22be7fd9fb986d4d42d7f36b0502fdf048830b7a) reads the translated labels and password warning from the catalog, and still checks every letter while leaving symbols shared with the English source to that existing path.
Carry its exact test patch with his author and date, retaining an edition's unrelated Korean glyph control; the independently qualified suite catalog pin is a separate change.
How found: the public correction merged during the reconciliation, the French rows supplied both labels, and a character-map audit identified only the source's U+25B8 in the affected primary font.
The real French, German, primary-letter and Korean controls all passed with the required catalog and font inputs.
Do not describe that primary-letter result as proof that every English menu symbol renders, or change fonts and product defaults merely to match the old test.

### Receiving tests must exercise the shared owner's actual bounds

Symptom: a receiving parser test rejects the deepest expected value even though the common library's own bound tests pass.
Cause: the receiving test assumes the former private backend's limit, such as 128 direct containers, while the shared owner admits 64.
Fix: retain the common production limit and adapt the receiver's boundary fixture to test admission at 63 and 64, refusal at 65 and the older 128 and 129, sibling recovery after refusal, hostile nesting and a small-stack traversal.
Keep the independent function-depth and node-budget tests; a direct-object parser cap may stop a nested function before its separate function guard is reached.
How found: the unchanged renderer sweep reported a failed 128-level positive, the shared byte reader declared 64 and already tested both sides, and the adapted receiver passed its parser, 512 KiB stack and fourteen function-limit controls.
Do not describe a receiver-test adaptation as a production parser repair or raise a common limit to satisfy its former private backend's fixture.

### A glyph name can number usage order rather than a character

Symptom: numbered glyph names produce plausible but incorrect letters even after a strict glyph-list text port.
Cause: a subset names its first used glyph C1, its second C2 and so on; an apparent C65 at code 65 is not evidence that it means A.
Fix: carry the font-wide consistency review and its later control-code-counter check with the original subject.
Keep strict AGL text reading separate from the lenient name lookup used to find an outline.
How found: the original numbered Type1 and Type3 receiver controls failed on a counter starting at code 1; the missing [review](https://github.com/storytold/pdfcraft/commit/8c892e65299473ce854d253d47ecf7d58c098dd2) rejects a numbered name below code 32 for the whole font.
All thirteen selected glyph-name and symbolic-font controls then passed.

### New byte loops must keep cancellation inside a wide row

Symptom: a packed, odd-width PNG-predicted image is repaired by a byte-row port, but the new loops no longer pass through the common bit reader's cancellation checkpoints.
Cause: the original app carried the image correction without the shared owner's per-open control object.
Fix: thread that existing control through every new filter branch, checking within a wide row as well as between rows, without changing decode or allocation bounds.
Keep the original predictor reference tests and the common cancellation tests in both default and unsafe builds.
How found: the three-way conflict showed the old PredictorRun and checkpoints against the new byte loops; the odd-width four-bit RGB receiver and all eight predictor controls passed after the integration, including the existing wide-row cancellation control.
Testing a patched dependency with cargo test -p can refuse because it is not a workspace member; testing its standalone manifest without the complete local patch set can instead select an uncached registry backend.
Use the shared crate's standalone test recipe with a disposable manifest copy and every resolved local patch, leaving source manifests and locks unchanged.
Compile the original new unit fixtures too: their parameter initializers may need the common-only control field even when the receiving application already compiles.

### A parser guard can stop recursion before the renderer reports it

Symptom: the original active-form guard fixes recursive copies in a resource-less form, but own-resource, pattern and Type3 recursion controls still miss the typed warning.
Cause: the shared syntax reader refuses an ancestor reference before a second FormXObject reaches the render guard.
Fix: retain the [original active-form subject](https://github.com/storytold/pdfcraft/commit/42b21e5362c99be04b3fd48c23ba58290a815987) with its author, then integrate the receiving parser separately.
Check a raw resource reference against the existing active-form identity before resolving it, and report only a known active form.
Keep parser cycle checks, complete resource-scope isolation and the existing per-page active set.
How found: a new independent repeated-draw witness first painted an extra recursive blue square; the original subject removed it and still allowed a later independent invocation.
The original warning controls then remained red although tracing showed only one form entry; the raw-reference integration made all twelve recursion, repeated-draw, pattern and default-color controls pass.
An explicit malformed resource naming a Pages dictionary is a separate negative: isolation prevents it borrowing the page's form, so it never attempts that recursion.
Do not label every unresolved object reference a recursion limit or undo resource isolation to reach a later guard.

### A repaired update must keep authentication and cancellation

Symptom: the shared reader opens an older valid xref while the editing model reads objects from a final cut-off update.
Cause: a successful older table never reaches the ordinary fallback path, and the first private repair subject lacks later authentication and object-header reviews.
Fix: carry the complete original recovery family, authenticate the named root first, require a rebuilt table's encryption state to match it, and accept recovered pages only when at least one is usable.
Retain the common decoder limits, per-open control, existing unlinked-xref repair identity and controlled fallback; do not copy the private Pdf::load over those APIs.
Reuse the controlled marker search and poll inside long digit, whitespace and junk runs in the new object-header detector.
How found: a complete receiving sweep left exactly four cut-off/header failures; the reviewed controlled port made all 683 renderer-library tests pass, including existing encrypted/wrong-password and trailing-data controls.
Default and unsafe common-unit runs also passed cancellation inside each long header run with uncancelled positive controls.
That library sweep still does not qualify the complete application or the other shared-library receivers.

### A focused success can run no tests

Symptom: a selected integration-test command exits successfully but reports zero tests.
Cause: the test module requires a feature absent from the focused command, even though the whole all-feature gate includes it.
Fix: inspect the module's feature guard, enable that feature and require the intended test names and a nonzero expected count in the receipt.
How found: the common PDF raster target ran zero controls with default features; the same frozen source ran all 29 controls with all features enabled.
Keep the first receipt as an unqualified attempt, and rerun the whole configured gate after the focused correction.

Symptom: the original Type3 rendering-mode correction is present, yet a Type3 glyph in mode 7 hides a later page fill.
Cause: the shared interpreter marks a text clip as shown before distinguishing outline glyphs from Type3 procedures, so ending the text object installs an empty outline clip.
Fix: mark the clip only in the outline arm; keep the empty-outline clip for spaces and keep reporting the Type3 rendering mode to text extraction.
How found: two shared-owner recording-device and pixel controls failed before the change, then passed beside fourteen existing interpretation controls; five receiving Type3 controls and strict selected Clippy also passed.
These component results do not qualify the complete shared revision or its receiving suite.

Symptom: a workspace gate passes while the changed PDF text control remains ignored.
Cause: the PDF-specific workflow supplies a fixture configuration and licensed external fonts that the workspace command alone does not enable.
Fix: read every workflow selected by the changed paths, provision its original hash-verified fixtures, use its configuration and runtime runner, and check actual executed totals before claiming coverage.
How found: an initial owner selection exited successfully with zero executed controls and one ignored control; enabling `craft_pdf_unicode_fixtures` and the six pinned fixture files produced the expected runtime failure.
A workspace result remains useful evidence for its recorded commands, but does not qualify an omitted dedicated workflow.

Symptom: the original combined fill/stroke patch fixes paths while a shared text run still composites its stroke over its fill.
Cause: the common interpreter's whole-run fill/stroke replay bypasses the imported per-glyph grouping branch.
Fix: put the implicit group around the outline run's replay boundary, preserving event order, text advances and clipping; Type3 procedures remain single-paint operations outside this outline group.
The reference must model one combined graphics object under ISO 32000-1/2 clause 11.7.4.4; two independent translucent graphics objects are a different operation.
How found: the font-enabled explicit knockout-group reference failed before the integration, then all 44 selected owner controls and 26 receiving controls passed, with strict selected Clippy and formatting checks.
These component results still require the full shared and receiving gates.


### A locked optional package is not the active feature graph

Symptom: an isolated read-only contract stops offline on a missing image-codec package, although its README says image decoding is excluded.
Cause: its separate lockfile records optional packages that Cargo still needs to resolve; it does not inherit the parent workspace's patch table.
Fix: inspect the shipping dependency's actual features and `cargo tree --edges normal,features` before changing a manifest or attributing the failure to a backend bypass.
When the codec is absent from that graph, cache the exact locked inputs separately, keep source and lock unchanged, then execute the original contract offline.
How found: the four read-only controls passed natively and in the WASM runtime after caching, while their normal graph contained no interpreter, rasterizer, writer or image codec.
Retain the failed attempt and bind a resumed workflow to the same frozen source and harness; a missing cache entry never qualifies skipped later jobs.


### A receiver can reject versionless edges inside a public shared crate

Symptom: the receiver's native and WASM checks pass, but cargo-deny rejects the common menu, UI and print crates for wildcard dependencies despite `allow-wildcard-paths = true`.
Cause: that exception covers normal and build edges only in private crates; public shared crates still need version requirements on their path and Git dependencies.
Fix: add the versions read from the existing package manifests and selected immutable Git lock entry in the shared owner, retaining every path, revision and feature.
Keep the receiver's ban and the shared crates' publication status unchanged.
How found: the unchanged whole receiver gate named the offending public edges; adding those existing constraints made the focused ban check pass without a lockfile change.
That focused result still needs complete shared-library and receiving gates on the resulting revision.
The [cargo-deny exception](https://embarkstudios.github.io/cargo-deny/checks/bans/cfg.html#allow-wildcard-paths) and [Cargo's multiple locations](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#multiple-locations) describe the policy and the source-plus-version form.
