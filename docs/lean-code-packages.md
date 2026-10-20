# Lean Code packages: the lc mark

## Main principle: prepare ahead of consumption

> Lean Code moves preparation upstream. Like pre-rendering or pre-staging, it prepares what the machine needs before consumption, avoiding repeated work while preserving the original material for people.

**Optimize the path of consumption.** Pre-processing transforms inputs in advance; pre-staging puts data where it will be needed; pre-rendering prepares a visual result before it is requested. Lean Code prepares a verified machine form while keeping the complete human-authored source available.

The objective is fewer bytes read and scanned, less parsing work and less working space where the consumer benefits. It applies both to compiler inputs and to runtime scripts, QML and settings. C/C++ comment removal reduces the compiler's input even when the executable is identical. Cached or compiled forms need their own measurements.

Measure actual reads, CPU time, elapsed time and memory for the operation concerned. Documentation and verification records outside that path do not negate avoided reads there; their storage and processing costs belong in separate build, update and footprint accounts. The principle identifies work to avoid; it does not substitute for measured results.

## Release requirement

Daniel's release rule, 18 October 2026: every package and ISO that the edition publishes goes through Lean Code in our pipeline. A package processed before distribution carries an **lc** mark so clients do not repeat the projection.

The first format is **lc1**, implemented in dpkg-stereo 0.1.6 and extended in 0.1.7. Older installed clients and development images need updating. Newly qualified development packages can use this format while migration of the remaining repository and the final ISO continues.

## Package contract

The binary control field is `Sparky-Lean-Code: lc1 <manifest SHA-256>`. In a Debian source control template, use the `XB-` prefix to carry a custom field into binary control, or let the final packaging step write the binary field directly. The usual package name, version ordering and APT update channel stay intact. A changed, previously published package must receive a new version; never replace the bytes of an existing release. [Debian user-defined control fields](https://www.debian.org/doc/debian-policy/ch-controlfields.html#user-defined-fields).

The manifest is `/usr/share/dpkg-stereo/lc/<package>/<architecture>.json`. It identifies the package, version, architecture, renderer and its source hash, and records each payload file's result, reason, checksum and mode. Architecture-specific paths avoid conflicts between 32-bit and 64-bit twins. Projected files also identify the exact authored text and the successful consumer check.

`lc1` certifies the **qualified installed-payload pass**. It does not claim that every format has a qualified adapter or that native compiler inputs were projected. Unknown formats, semantic directives, licences, documentation, self-reading files and files outside the current size bound retain their explicit coverage reasons. Unqualified formats remain work. The separate requirement to project C/C++ inputs before compilation still applies to our builds and needs its own build evidence.

A client accepts only a manifest bound by the installed package's control field and matching its package identity and supported proof format. It skips rendering that package. Older renderer provenance remains valid under the same `lc1` contract; upgrading the client does not invalidate every earlier build. Unknown formats or corrupt markers do not authorize skipping: they are reported and the normal local qualification path runs. APT's normal archive authentication remains the trust mechanism; the lc mark is not a signature or a security boundary.

## Configuration, documentation and debugging

The build projects a disposable staging tree before final checksums and package assembly. Its lean configuration is therefore dpkg's original baseline. Build-time records never enter the local-projection conffile restoration index. A user's changes remain subject to dpkg's normal configuration rules. [Debian configuration-file policy](https://www.debian.org/doc/debian-policy/ch-files.html#configuration-files).

The full authored text of changed files goes in a separate `<package>-lc-hr` package at the exact version and architecture. It is required alongside the runtime package in the repository, but is not a runtime dependency and does not go into the ISO by default. The first online update fetches the authored settings; `dpkg-stereo --hr /path` can retrieve other originals. Each retrieved file is checked against its recorded authored-text hash. The usual documentation path and the one-line pointer remain available.

`--resolve` reconstructs a lean file from its exact authored text and refuses a mismatch, so an updated renderer cannot silently point an old error at the wrong line. `--verify` checks build-time projections too; `--deep` checks the complete recorded payload. `--restore` reverses local projections to the distribution baseline. For a build-time lean package that baseline is already MR; `--hr` is how to read the full authored text.

## Build and release order

1. Build from authoritative source and retain the source package and native build evidence.
2. Finish staging, package identity, provenance and copyright notices.
3. Run the shared `lean.release build-tree` step. It validates projections, prepares the exact HR companion, writes the `lc1` manifests, regenerates checksums and builds the archives. This replaces the final `dpkg-deb` call, before `.changes` and signing.
4. Verify the final archives, complete payload coverage, checksums and required HR companions before repository signing. The repository publisher and sync helper enforce this gate. They also reject unmarked carried packages; those require a properly versioned edition rebuild, not a marker added to an upstream archive.
5. Build release ISOs with Lean Code enabled. The pre-squashfs pass verifies the projected filesystem and records its report. The final ISO receives an `lc1` build attestation bound to the ISO and report hashes. Verify it with `lean.release check-iso` before upload, and publish the evidence alongside the ISO.

An unprojected comparison ISO requires an explicit benchmark purpose and a `-nolean-` filename. It cannot receive a release attestation. General-purpose remastering retains its separate, optional policy.

The ISO attestation verifies the build's evidence and artifact hashes. It does not replace boot, installation, hardware or performance tests. File bytes removed, package and ISO size, update CPU time, cold starts and warm starts are separate measurements.

## Java, Kotlin and native build inputs

The development tooling adds compiler-backed Java and Kotlin adapters: Java uses the JDK lexer,
and Kotlin uses the pinned Kotlin compiler lexer. Documentation comments, licences, operational
directives and string contents remain intact. Kotlin newline and token-adjacency semantics are checked.
The Flat Headset recipe qualifies JDK 17 with Kotlin 2.4.0 and then runs the actual Gradle build and headset tests.
Missing compiler tooling is a recorded refusal, never a successful optimization.

Native source checks must also cover generators that read comments or textual layout.
During the 20 October migration, XScreenSaver's resource validator rejected inserted line directives, and SDL's manual generator needed the original header documentation.
The 0.1.9 candidate leaves files with structured documentation or translator annotations unchanged and records additional package-specific preservation patterns in the retained source.
This preserves those consumers while other qualified files still receive the pre-compilation pass.
The [maintainer skill](../skills/lean-code/SKILL.md#native-source-consumers-migration-findings-20-october-2026) gives the preparation command and failure rules.

GLSL shaders remain unchanged until a shader-specific checker is qualified. The 0.1.12 migration candidate also repairs earlier install-time shader projections: it restores exact originals, leaves user edits intact and retries when the matching original is unavailable. Updating the checker alone would leave those old projections in packages that were not upgraded. This recovery is part of qualifying an existing installation; it does not mean the full repository migration has finished.

The diagnostic resolver (sometimes called our “decompiler”) maps a location in lean code back to
the matching complete authored source. It checks source identity and hashes before resolving.
C/C++ builds preserve authored line numbers through `#line`; Java/Kotlin builds retain a separate mapping
and exact source copies. This is source recovery from recorded originals, not reconstruction of lost comments from a binary.

For installed packages, use `dpkg-stereo --hr /path/to/file` and
`dpkg-stereo --resolve /path/to/file:LINE[:COLUMN]` with the matching HR package available.
Flat Headset's build documentation gives the corresponding `tools/resolve-lean.py` command for Android.
The APK's pre-compilation report is separate from the Debian `lc1` installed-payload marker.
