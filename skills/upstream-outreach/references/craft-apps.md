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

AniCraft requires crates.io-only dependencies and a cargo-deny gate.
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
