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

PhotoCraft [#7818](https://github.com/storytold/photocraft/pull/7818) was closed on 2026-11-05 after the author left FredApps' 2026-10-19 requested changes unanswered for over two weeks.
The maintainer invited a current-main rebase and a reopened or fresh PR.
That historical closure is not today's thirty-day rule.
FredApps corrected his own point 2: PNG normalization remains a maintainer decision; he withdrew the claim that the cited issue promised unchanged stored pixels.
Preserve the correction when answering the review.

The two CodeRabbit findings were truncated MPO entries silently losing damage reporting and Duotone stereo exports bypassing ink rendering.
Confirm each against the submitted head, then cite the fixing commit and a regression, or explain with measured evidence why it no longer applies.

## Authorship and assistance are different claims

Read the exact wording before declaring an attribution-policy conflict.
Craft core rule 15 says a pull request does not say an agent wrote it; acknowledging assistance does not make the assistant its author.
Keep the person as author and accountable reviewer, with no agent author/co-author or “Generated with” line.
Retain the instructed `Assisted-by:` commit trailer and acknowledge AI assistance once in the fresh pull request description; do not repeat it in replies.
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

## Duotone pixels match, but the warning counts a virtual layer

PhotoCraft's stereo ink rendering initially matched ordinary export pixels but reported that two layers were flattened for a single-layer Duotone document.
The RGB preparation adds a temporary ink adjustment, which the flat renderer counts as another layer.
The ordinary Duotone exporter already removes that artificial-layer warning; reuse its policy in the stereo path only when the same preparation was used.
A regression comparing ordinary and stereo warnings failed on MPO before that correction.
Check the ink-to-RGB notice and actual RGB layer-loss notice separately, along with exact PNG colors and the JPEG encoder's bounded color difference.
Do not hide unrelated fidelity warnings or suppress flattening notices for ordinary RGB documents.

After building the complete CI feature graph, use the same workspace, features and test targets with a nextest filter for focused checks when appropriate.
A package-only default-feature invocation can select a different graph and rebuild shared dependencies; it is useful coverage when intentional, and is not a substitute for the full receiving gate.
