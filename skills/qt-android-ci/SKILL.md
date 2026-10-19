---
name: qt-android-ci
description: >-
  Reproduce Qt Multimedia Android CI in a headless emulator with exact Qt/NDK/ABI inputs and complete QTest row evidence.
---

# Qt Android CI reproduction

## Working recipe

1. Read the failing Coin job and record its Qt/FFmpeg revisions, API, ABI, NDK and decoder before choosing a local setup.
2. Follow the linked recipe, verify every expected data row ran, and retain full runner/QTest logs and source diffs.
3. Return matched and unmatched environment dimensions. An x86_64 software decode does not qualify ARM or a physical MediaCodec path.

Read [Run Qt's Android tests locally](references/run-local.md) for the test recipe and [Build prerequisites](references/build-environment.md) when the matching host/Android Qt installation is not available.

Audit the requested Coin configuration before selecting versions.
Record Qt revisions, Android API, ABI, NDK, FFmpeg flags and test runner.
An x86_64 run does not establish 32-bit x86 behavior.
Use Qt's LGPL FFmpeg recipe, including its OpenSSL stub rewriting; a product-specific FFmpeg is a different experiment.

For a comparison, export unchanged tests from each revision and verify production libraries are identical before sharing one installation.
Keep the backend, Qt platform, emulator and test environment fixed.
Preserve the source diff and full QTest/runner logs.
A runner error before test launch is not a test result.
A matching QTest assertion and test-process SIGABRT are stronger evidence than a nonzero shell exit alone.

To re-enable coverage, enumerate the expected data rows.
Assert every row ran and passed; zero failures with skipped or missing media rows is insufficient.
Report software/hardware decoding and the tested ABI.
Keep remaining warnings visible without treating them as failed assertions.
Before proposing a change, search Gerrit for open changes to the same test file and read their CI results.
A maintainer's own change may already re-enable the coverage, and its failing Coin configuration (for example an Android API level with a hardware decoder) is the case to reproduce.

The scripts run as the caller in named containers, force KVM and headless SwiftShader, cap CPU use, and expose a configurable storage reserve. Use the active workspace disk floor; the original recipe used 15 GiB, which must not override a newer explicit storage decision.
Supply paths and an existing compatible build image; do not install tools on a desktop host as part of this recipe.
Register rebuildable artifacts if the project has a registry, preserve evidence and local commits, and remove completed build intermediates.
Follow the user's milestone and publication boundaries.
A successful local run does not authorize a Gerrit push or comment.

Documentation follows Sparky Stereo OS's CC BY 4.0 terms; accompanying code uses GPL-2.0-or-later.
Keep upstream licenses with any redistributed Qt, Android, FFmpeg or OpenSSL material.
