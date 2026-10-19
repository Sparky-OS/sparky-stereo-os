# Run Qt's Android tests locally

This recipe was exercised with Qt 6.13 dev, Android 9/API 28 x86_64, NDK r27c and Qt's LGPL FFmpeg 9.0.2 build.
It uses the real androidtestrunner, Android platform plugin and FFmpeg backend.
It does not emulate Coin's original 32-bit x86 job or all its provisioning and packaging jobs.

## Prepare once

Use a Linux Docker daemon with KVM access.
Supply an existing container image with a compatible C++ compiler, CMake/Ninja, Python 3, Perl, make, Git, unzip, patch and the emulator's Linux runtime libraries.
The measured run used openSUSE/GCC 16.2.1, not Coin's RHEL image.
The scripts do not install packages or build an image.
Set `QACI_RESERVE_GIB` to the active workspace floor; the original default is 15 GiB.
Allow another 3 GiB above that floor before a test build. On the designated expendable build disk in the current studio, the floor is 2 GiB (`QACI_RESERVE_GIB=2`).
Allow roughly 1.2 GiB per test tree.

[Build prerequisites](build-environment.md) lists the audited source pins, SDK layout and Qt/FFmpeg build commands.
Use these paths inside one build storage directory; Qt installations and toolchain files retain their paths:

```text
src/qtmultimedia/          selected source revision
install/host/             host Qt tools, including androidtestrunner
install/target/           Android QtBase, QtShaderTools and Qt Multimedia
install/ffmpeg-x86_64/     Qt CI FFmpeg build
sdk/                      SDK, emulator and API 28 Google APIs x86_64 image
sdk/ndk/27.2.12479018       symlink to the NDK below
toolchains/android-ndk-r27c/
avd/                      qt_api28_x86_64 AVD
```

## Build and run

Set absolute paths. `QACI_IMAGE` is your prepared image and `QACI_JDK` is an existing JDK 21 directory, mounted read-only.
The Docker host may be local or selected through the standard `DOCKER_HOST` variable.

```bash
export QACI_WORK=/absolute/build-storage/qt-android-ci
export QACI_IMAGE=your-existing-build-image:tag
export QACI_JDK=/absolute/path/to/jdk-21
export QACI_SOURCE="$QACI_WORK/src/qtmultimedia/tests/auto/integration/qvideoframebackend"
# Paths below are relative to the skill directory.
bash scripts/container.sh build
bash scripts/container.sh run
cat "$QACI_WORK/evidence/frame-test/qtest.txt"
cat "$QACI_WORK/evidence/frame-test/exit.txt"
```

Optional settings: `QACI_BUILD` and `QACI_LOGS` select separate directories for each experiment; `QACI_HOME` selects the container user's home; `QACI_AVD` selects the API 28 x86_64 AVD.
If the SDK contains links to an external SDK directory, set `QACI_SDK_SOURCE` so it is mounted read-only.
For a remote Docker daemon, set `QACI_KVM_GID` to the daemon host's KVM group ID.
Otherwise it is read from `/dev/kvm`.
All bind paths must exist on the daemon host. `QACI_ARTIFACTS`, if supplied, receives the container name and test build directory; register other created folders under your project's cleanup rules.
The image is pre-existing and never registered for deletion by this script.

The native build is RelWithDebInfo. `QT_BUILD_TESTS=ON` selects debuggable APK packaging: release APKs cannot be used with the runner's `run-as`.
The SDK's NDK symlink lets Gradle strip packaged libraries; otherwise the APK can exceed the runner's installation timeout.
The offline Gradle warm-up avoids a cold-start timeout in its package-namespace query.

The run forces `QT_QPA_PLATFORM=android`, `QT_MEDIA_BACKEND=ffmpeg` and `QTEST_ENVIRONMENT=ci`.
It boots headlessly with KVM, two cores, 4 GiB RAM, SwiftShader and no audio.
Both Android boot properties, API and ABI are checked before deployment.
No host display or audio socket is mounted.

## Compare patch sets

For change 778399, PS8 is `48835d29869501bbc416ef52901bee4cd7b6eead` and PS9 is `1b10d5488200ee0c71f5db79512a6fca7dd84853`.
Fetch the public Gerrit refs `refs/changes/99/778399/8` and `/9` if needed.
Confirm their only repository difference is the test's skip placement before sharing the PS9 libraries.
Export each test subtree into a separate source directory with `git archive` and `tar --strip-components=4`, then select it with `QACI_SOURCE` and use separate build/log directories.
Never label a locally altered test as an unchanged patch set.

Observed results on this configuration:

| Source | Expected evidence |
|---|---|
| PS8 | QTest::fetchData assertion: “Test data requested, but no testdata available.”; test-process SIGABRT; 1 passed, 1 failed, 1 skipped; runner 253 |
| PS9 | 6 passed, 0 failed, 3 skipped; runner 0; luminance skip in the data function |
| PS9 with the four Android QTBUG-118571 exclusions removed | 15 passed, 0 failed, 0 skipped; runner 0, including three luminance rows and threaded OpenGL rendering |

Inspect `qtest.txt`, `runner.log`, `crash.log`, emulator readiness and the recorded exit together.
Exit 253 alone only says the runner did not receive an exit-code file.
Raw crash logcat can include unrelated system processes.
For the skip-removal candidate, validate all expected rows with `python3 scripts/check-results.py "$QACI_LOGS/qtest.txt" "$QACI_LOGS/exit.txt"` inside the container (use the default log directory if QACI_LOGS is unset).
This checker intentionally rejects the PS8/PS9 baseline results.
The last case used software decoding; it does not certify MediaCodec or physical Android devices.
Temporary-file warnings remained despite all assertions passing.

After saving logs, source revisions/diff, APK hashes and small CMake/Ninja records, remove the selected test build directory.
Retain dependencies only for the next authorized step.
The scripts remove their container, shut down the emulator and the runner uninstalls the test package.
Logs in the same directory are overwritten by a later invocation: choose a new directory when preserving comparisons.

Qt's [commit policy](https://wiki.qt.io/Commit_Policy) and [branch rules](https://contribute.qt-project.org/quips/16) govern a proposed upstream change.
The tested skip-removal candidate uses `Task-number: QTBUG-118571` and `Pick-to: 6.12`; publishing remains a separate review decision.
