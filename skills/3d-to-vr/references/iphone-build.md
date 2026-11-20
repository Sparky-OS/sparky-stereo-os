# Building Flat Headset for iPhone from Linux

**For the contributor: write and test portable code on Linux, compile the native application on a standard hosted macOS runner, then sign and install from Linux.**
Check freshness first: source workflows and local gates checked 2026-11-20.
The first native proof target and workflow are implemented.
[Hosted run 44690357195](https://github.com/Sparky-OS/flat-headset/actions/runs/44690357195) passes every step for commit 306c59c: the portable tests, the native app build, the arm64 and unsigned checks, the packaging and the artifact upload.
The downloaded artifact was checked on Linux: the checksum, the manifest entry, only our own files inside, an arm64 program for iOS 16.0 and later with no code signature.
Signing, installing and a launch on a phone are not yet established.

## Working recipe

1. Work in the receiver's repository on Linux; leave Android sources unchanged when adding its `ios/` target.
2. Run the portable generator's C++ tests, the ten-language native catalog check, the tooling negative controls and actionlint on the new workflow.
   UIKit and Metal compilation belong to the hosted Mac; missing UIKit on Linux is a recorded boundary, not a passing native compilation.
3. Have the authorized publisher push the reviewed branch to our public repository.
   The first workflow step prints `xcodebuild -version`, `xcodebuild -showsdks` and the hosted image name/version, then checks that the installed iPhoneOS SDK meets the deployment-target version floor.
   Use the image's default Xcode as it stands, with no SDK download to the Linux station.
4. Compile the native arm64 app with the literal command below, `CODE_SIGNING_ALLOWED=NO` and no development team.
   A workflow must not contain credentials, certificates, provisioning profiles or an Apple account.
5. Package the built application under `Payload/FlatHeadset.app` as `FlatHeadset-unsigned.ipa` and keep its SHA-256 and receiver manifest entry in the same artifact.
   This is a development build artifact, not an installable signed application or a store submission.
6. Read the run for the exact pushed commit; a local lint pass, an absent run or a run for another SHA is not a hosted build result.
   Fix a failing run before starting the next program; three failures at the same step with no cause found are a stop to report.
7. Once the three programs exist, combine their reviewed artifact entries into a private manifest with the intended phone's UDID and use the [Linux renewal helper](../scripts/iphone-renew.py).
   Account authentication and phone prompts remain the person's steps; signing needs no SDK on Linux.

[GitHub's billing documentation](https://docs.github.com/en/actions/concepts/billing-and-usage) says standard hosted runners are free for public repositories.
This does not make arbitrary larger/private runners free, nor justify unbounded artifact retention.
The proof workflow selects the standard `macos-15` image, retains artifacts for seven days, has a twenty-minute timeout and builds with four jobs.
The app's deployment minimum is iOS 16.0; the installed SDK version is printed instead of assuming it matches the deployed OS version.
Keep that value in a project-specific variable such as `FLAT_HEADSET_IOS_MIN`, not a job-level `IPHONEOS_DEPLOYMENT_TARGET` that Apple Clang consumes during the macOS host tests.
Pass `IPHONEOS_DEPLOYMENT_TARGET="$FLAT_HEADSET_IOS_MIN"` only as an argument to the native iPhone `xcodebuild` command.
The first [hosted run](https://github.com/Sparky-OS/flat-headset/actions/runs/44687332888), checked 2026-11-20, used runner image `macos-15-arm64`, reported `ImageOS=macos15` and image version `20261118.0550.1`, and selected Xcode 16.4, build 16F6.
Its SDK list was DriverKit 24.5, iOS/iOS Simulator 18.5, macOS 15.5, tvOS/tvOS Simulator 18.5, visionOS/visionOS Simulator 2.5 and watchOS/watchOS Simulator 11.5.
The host compiler identified itself as AppleClang 17.0.0.17000013.
These are observed values for that run, not a promise about future contents of the runner label.
The iOS 18.5 SDK passes this proof's 16.0 floor; Xcode 16.4 does not meet FreeRDP's documented Xcode 26+ requirement, which the later core workflow must resolve on an appropriate hosted image.
Reading [Apple's SDK agreement](https://www.apple.com/legal/sla/docs/xcode.pdf) is not legal advice; Daniel decides the applicable licence questions.
The selected compile runs on hosted Apple machines running macOS, rather than moving Apple's SDK onto the Linux workstation.
The prior Linux cross-compiler probes remain useful evidence in [the iPhone reference](iphone-arm.md); they are not the selected SDK build route.

## The first receiver target

The app is named **Flat Headset** on iPhone, exactly as on Android.
Its Xcode project is `ios/FlatHeadset.xcodeproj`, shared scheme `FlatHeadset`, bundle ID `org.sparkyos.flatheadset`.
The smallest proof displays a generated full-panel left/right image in landscape with Metal, using `UIScreen.nativeBounds` for physical pixels.
A portable C++ generator supplies the grid, complete eye borders, pixel-circular geometry and L/R marks.
The fragment shader reads the corresponding texel without texture rescaling; this is not lens calibration.
Xcode compiles the `.metal` source into the application's default Metal library.
The native Objective-C++ shell owns the window, drawable, texture and command submission, and shows localized failure text.
There is no desktop reception, pairing, lens profile or tracking in this first generated-picture proof.
The eventual receiver still requires KDE Connect pairing, FreeRDP/KRdp and the Android viewer mathematics.

The workflow's build command is:

```sh
xcodebuild -project ios/FlatHeadset.xcodeproj -scheme FlatHeadset \
  -configuration Release -sdk iphoneos -destination 'generic/platform=iOS' \
  -derivedDataPath "$RUNNER_TEMP/flat-headset-build" -jobs 4 \
  IPHONEOS_DEPLOYMENT_TARGET=16.0 \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY='' \
  DEVELOPMENT_TEAM='' build
```

After checking the executable's arm64 architecture and absence of signing/provisioning data, copy the app into a temporary `Payload` directory and package it with `ditto -c -k --keepParent`.
Do not use `xcodebuild -exportArchive` as an unsigned packaging shortcut; its distribution/export flow adds provisioning concerns this step deliberately does not need.
The artifact is named `FlatHeadset-unsigned-COMMIT` and contains the IPA, `SHA256SUMS` and `flat-headset-artifact.json`.
The JSON's `apps` array contains one `flat-headset` entry with `path`, `sha256` and `bundle_id`, plus the build commit outside that array.
It is not yet the three-app renewal manifest and deliberately has no phone identifier.
Keep the fixed bundle IDs across renewal, and verify the SHA-256 after download before combining the three entries privately.

## Upstream project reconciliation

Read the actual revision before copying a CI command; a runner called macOS can still be building Android.

| Program | iPhone source baseline and project | Actual upstream command or absence |
| --- | --- | --- |
| Our KDE Connect | KDE Connect iOS a3036396; `KDE Connect.xcodeproj`; embedded Swift package dependencies, not a root application Swift package | `.gitlab-ci.yml` builds the iPhone simulator with the exact command below. It does not establish an arm64 device IPA. |
| Our Cardboard profile program | Cardboard 8bd424da; `sdk/sdk.xcodeproj`, `hellocardboard-ios/HelloCardboard.xcodeproj`, root workspace and Podfile | `.github/workflows/Android-CI.yml` uses macOS but runs `./gradlew :sdk:assemble`, `./gradlew :hellocardboard-android:assembleDebug`, `./gradlew check`. No upstream iOS `xcodebuild`/`swift build` CI command was found. Google's iOS quickstart says `pod install`, open the workspace and Run. |
| Flat Headset's eventual RDP core | FreeRDP 3.28.0, 5370fb26; CMake generates the iOS Xcode project | `macos.yml` runs `./scripts/bundle-mac-os.sh` for the desktop build. `docs/README.ios` separately documents CMake's Xcode generator and `cmake --build`; no dedicated iOS CI line was found. The minimal Metal proof does not yet link this core. |

KDE Connect's exact simulator build line, with its upstream plugin-validation choice retained as evidence:

```sh
xcodebuild build -project 'KDE Connect.xcodeproj' -scheme 'KDE Connect' \
  -destination 'platform=iOS Simulator,name=iPhone 17,OS=latest' \
  -skipPackagePluginValidation CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY=""
```

[FreeRDP's iOS instructions](https://github.com/FreeRDP/FreeRDP/blob/5370fb26fbf034ecd11d3026b6ad639b5fff493f/docs/README.ios) request Xcode 26+, CMake, OpenSSL and FFmpeg.
They generate with `cmake -S client/iOS -B build/ios.client.build -DCMAKE_TOOLCHAIN_FILE="$PWD/cmake/ios.toolchain.cmake" -DPLATFORM=OS64 -DDEPLOYMENT_TARGET=15.0 -DCMAKE_XCODE_ATTRIBUTE_DEVELOPMENT_TEAM=XXXXXXXXXX -G Xcode`, then `cmake --build build/ios.client.build`.
That team-bearing example is an upstream quotation, not our unsigned workflow.
The later core workflow must remove the team, disable signing, bound build parallelism, print the actual SDK and apply the iOS 16 deployment target.
Its dependency pins are OpenSSL 4.0.1 and FFmpeg n8.1; the initial SDK-free OpenSSL 3.6.0 probe was not that dependency configuration.
Do not start that feature step until the generated-picture app's hosted workflow is green.
Next come the paired RDP receiver, our KDE Connect with virtualmonitor, then the Cardboard profile program, each with its own green workflow before the next.
Tracking belongs later to **iStereoVR** and **StereoDroidVR**, outside Flat Headset.

## Ten native languages

Every added native string ships in en, pl, pt-BR, fr, de, es, ja, ko, zh-Hans and zh-Hant.
The latter three spelling differences map the edition's pt_BR, zh_CN and zh_TW catalogs to iOS resource names.
The app display/name keys remain Flat Headset in all ten; failure messages are translated.
Check missing, extra, duplicate and empty keys, plus keys used by native code.
A negative control that removes one Spanish key must fail the same checker, not a parallel imitation of it.
Coverage proves presence, not a native speaker's acceptance or on-phone fallback behaviour.

## Traps

1. **Symptom:** local tool probes stop at `UIKit/UIKit.h` or an Apple SDK prerequisite and the whole iPhone route appears blocked.
   **Cause:** the compile was assumed to happen on the Linux workstation.
   **Fix:** keep Linux editing and portable tests, compile the native target on the selected standard hosted Mac, sign on Linux later.
   **How found:** the SDK-free compiler boundary followed by the hosted-build continuation; run 44688342867 now proves the native compile; packaging and phone execution remain separate checks.
2. **Symptom:** a green upstream macOS job is treated as proof of an iPhone app.
   **Cause:** Cardboard's job builds Android and FreeRDP's job builds the desktop client; KDE Connect targets a simulator.
   **Fix:** record exact commands and build an explicit arm64 `iphoneos` target.
   **How found:** reading the three pinned workflow files and FreeRDP's iOS instructions.
3. **Symptom:** an IPA name exists but its bundle is signed, provisioned, misnamed or has the wrong bundle ID.
   **Cause:** packaging alone says nothing about the application inside it.
   **Fix:** validate compiled metadata, executable architecture, signature/profile absence and hash before keeping the artifact.
   **How found:** synthetic package tests accept the expected metadata and reject a provisioning entry or unexpected bundle ID; the real IPA remains a hosted-run result.
4. **Symptom:** a phone shows cropped borders or a noncircular grid despite a successful build.
   **Cause:** point coordinates or the three-times backing store were used instead of physical drawable pixels, or the shader resampled the eyes.
   **Fix:** size the drawable and source texture to native landscape pixels and read one source texel per destination pixel; verify borders and circle through the device separately.
   **How found:** the earlier physical-panel correction and portable full-border/pixel-radius tests; Metal and phone verification remain pending.
5. **Symptom:** a localization gate stays green when a language silently falls back to English.
   **Cause:** comparing only existing directories does not require all ten catalogs.
   **Fix:** enumerate the ten required iOS locale names and the complete key set, then remove one real translated key as a negative control.
   **How found:** the native catalog checker and missing-Spanish-key test.
6. **Symptom:** Clang rejects a width overflow guard as always false on a 64-bit host.
   **Cause:** a uint32 width was compared against a size_t maximum divided by four.
   **Fix:** after rejecting zero width, compare the size_t maximum divided by width with four; retain capacity/stride guards and compile with warnings as errors.
   **How found:** Clang 21.1.8's `-Wtautological-constant-out-of-range-compare`; the corrected generator and tests pass without suppressing the warning.

7. **Symptom:** `using sysroot for 'MacOSX' but targeting 'iPhone' [-Werror,-Wincompatible-sysroot]` at the portable generator's first file.
   **Cause:** job-level `IPHONEOS_DEPLOYMENT_TARGET=16.0` leaks into Apple Clang while CMake selects the macOS SDK for a host test executable.
   **Fix:** keep the version in `FLAT_HEADSET_IOS_MIN`; pass the Apple deployment setting only on the native `xcodebuild` command, retaining warnings as errors and real host tests.
   **How found:** run 44687332888 prints the inherited variable, macOS SDK and exact compiler failure; catalog/tooling checks and both plutil lints passed before it.
   An SDK-free Clang 21.1.8 Darwin-driver `-###` probe selects `arm64-apple-ios16.0.0` with the old variable and `arm64-apple-macosx15.0.0` with the corrected workflow environment; no target compilation or Apple files are involved.
   Run [44688342867](https://github.com/Sparky-OS/flat-headset/actions/runs/44688342867) confirms the corrected host tests and native iPhone build both pass on the same Xcode 16.4 image; its next step fails at the architecture-check invocation.

8. **Symptom:** `lipo: unknown architecture specification flag` followed by the app executable path during `-verify_arch`.
   **Cause:** `-verify_arch` consumes the following architecture names, so the executable placed after `arm64` is interpreted as another architecture.
   **Fix:** use `xcrun lipo "$app/FlatHeadset" -verify_arch arm64` with the input first.
   **How found:** run 44688342867 prints `Mach-O 64-bit executable arm64`, then the error and `lipo <input_file> <command>` usage; the native build has already succeeded.
   Linux LLVM's lipo accepts the corrected invocation on an SDK-free arm64 Mach-O object and rejects an x86_64 requirement; this does not replace the hosted Apple-tool check.
9. **Symptom:** an unsigned-artifact gate accepts every nonzero `codesign --verify` result.
   **Cause:** signature verification failure can mean unsigned code, damaged signed code or a tool failure.
   **Fix:** retain and print the diagnostic, set `LC_ALL=C`, reject successful verification and accept failure only when the entire diagnostic is the app path followed by `code object is not signed at all`, a newline and `In architecture: arm64`.
   **How found:** review of the packaging step after the lipo failure; controlled command responses exercise unsigned, valid signed, damaged, missing-tool, empty-error and nested-code errors against the actual workflow shell.
   Apple's [code-signing error definitions](https://github.com/apple-oss-distributions/Security/blob/main/OSX/libsecurity_codesigning/lib/CSCommon.h) distinguish unsigned code from invalid signatures.
   No signature is removed to make this gate pass; run 44689690224 supplies the real two-line diagnostic.
   Its second line was omitted by the first exact-match gate and must be retained, as trap 10 describes.

### Packaging audit after the native compile

Reviewed 2026-11-20: the compiled app path in run 44688342867 matches the packaging input and `FlatHeadset` executable name.
[Apple's archive recipe](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution) uses `ditto -c -k --keepParent`; passing `Payload` as the source preserves the `Payload/FlatHeadset.app` layout expected by the manifest reader.
The manifest uses Python plistlib, which handles the binary plist produced by Xcode; its tests passed on the hosted Mac, including its SHA-256 helper.
It writes the JSON and SHA256SUMS next to the IPA in `ios-artifact/`, the directory passed to the pinned [upload-artifact action](https://github.com/actions/upload-artifact/tree/ea165f8d65b6e75b540449e92b4886f43607fa02).
The IPA is already a ZIP, preserving its executable modes inside the artifact's outer ZIP.
A Linux fixture checks these paths, a binary plist, the manifest digest and `sha256sum -c`; substitutes for codesign and ditto test shell control flow only.
Do not describe the native build as an uploaded or installed program until those later checks actually pass.

10. **Symptom:** the unsigned gate says it cannot establish unsigned status even though codesign reports `code object is not signed at all`.
    **Cause:** codesign appends `In architecture: arm64` on a second line, but the expected string and the original synthetic fixture contained only the first line.
    **Fix:** compare the whole captured diagnostic with `"$app: code object is not signed at all"$'\nIn architecture: arm64'` under Bash, retaining LC_ALL=C and rejection of successful verification.
    **How found:** [run 44689690224](https://github.com/Sparky-OS/flat-headset/actions/runs/44689690224) shows both lines after a successful native build and lipo check.
    A fixture extracted from that log, with only the temporary app path substituted, fails the old gate and passes the corrected gate.
    Reject a missing architecture line, a different architecture/path, additional or nested-code diagnostics, damaged signatures, successful verification and tool errors.
    Bash command substitution removes trailing newlines; the internal newline and both complete lines remain part of the exact match.
    The full packaging shell passes controlled Linux fixtures; the actual ditto archive, manifest from compiled metadata and artifact upload still require a hosted run.

The remainder was re-audited after run 44689690224: the compiled app path and executable match the packaging input; the source plist's literal display name and Xcode's product/deployment settings match the manifest requirements.
The hosted tooling test already exercised the same Python manifest and hashing code successfully.
The ditto Payload-root invocation, sibling manifest paths and upload-artifact directory remain as in the packaging audit above; no further defect was identified by this inspection.

## FreeRDP core build after the green native proof

Start from the merged skills main branch and the green receiver commit before adding the next build.
Run 44690357195's artifact was independently downloaded and checked: SHA-256 `3bbe7cb9539fea2db09d4e8532000a0826c4080660b59f039ca3640ca0304729`, arm64 executable, LC_BUILD_VERSION platform iOS with minimum 16.0 / SDK 18.5, no LC_CODE_SIGNATURE, and only the app's expected files and ten locale directories.
That establishes the unsigned native build route; it is not a phone launch or a received desktop.

The receiver's `ios/Core/sources.json` pins FreeRDP 5370fb26 (3.28.0), OpenSSL 4.0.1 and FFmpeg n8.1 with archive hashes.
The latter two match that FreeRDP revision's `cmake/DepVersions.cmake`.
`ios/Tools/fetch_core_sources.py` validates every hash before extraction and refuses existing destination source directories.
`ios/Tools/build_core.sh ios SOURCES BUILD` compiles static dependencies and the portable core with four jobs, using OpenSSL's own `ios64-xcrun` target and FFmpeg's explicit arm64 iPhoneOS sysroot/VideoToolbox options.
CMake searches target dependency and SDK roots for headers/libraries/packages; pkg-config sees only the target prefix.
Apple's SDK stays on the hosted machine and is not copied into the core artifact.

The separate `iphone-core` job uses `macos-26` because [the hosted image inventory](https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md), read 2026-11-20, supplies Xcode 26 or newer; its actual version is still printed and checked by the job.
The existing macos-15 generated-picture app job stays separate.
The core target includes client-common, TLS/authentication, FFmpeg H.264/HEVC and drdynvc/rdpgfx/disp/cliprdr channels.
Its link probe pulls in context creation, channel registration, H.264 lifecycle and OpenSSL/FFmpeg symbols.
The Linux `host` mode builds the same pinned dependencies and executes that probe without network access; the iPhone mode links it and checks arm64 and absence of a signature, without executing on a phone.
Only the iPhone mode compiles the VideoToolbox path; hardware decoding, software fallback behavior and zero-copy remain separate receiver tests.

The `FlatHeadset-core-arm64-COMMIT` artifact is a development archive of third-party headers/static libraries, licenses, source lock, build commit/configuration and the unsigned link probe.
It is not an IPA and must never be added to the renewal manifest.
The first core hosted run compiled and linked successfully but stopped at the probe-path check; an uploaded core artifact is still pending.
After the complete job is green, integrate authenticated pairing/certificate pinning and RDP lifecycle into the receiver, then decode-to-Metal and the Android viewer mathematics.
KDE Connect and the Cardboard profile program follow the receiver in the brief's order.

### Core build traps checked locally

- **Symptom:** the Linux host analogue stops at `Failed to find all ICU components` in WinPR's CRT configuration.
  **Cause:** WinPR uses ICU on Linux but Foundation on Apple platforms when built-in Unicode conversion is disabled.
  **Fix:** install libicu-dev in the Linux test container; keep Foundation as the native iPhone route instead of changing Unicode behavior to satisfy the host build.
  **How found:** the host CMake failure and `winpr/libwinpr/crt/CMakeLists.txt` at the pinned revision.
- **Symptom:** an upstream iOS dependency build runs unrestricted `make -j` or enables FFmpeg audio components that were not built.
  **Cause:** the upstream UI superbuild has different parallelism and dependency defaults from this receiver-core target.
  **Fix:** use explicit four-job commands and a declared video-only dependency configuration; desktop audio remains on the PC.
  **How found:** reading client/iOS/cmake/ExternalOpenSSL.cmake, ExternalFFmpeg.cmake and ExternalFreeRDP.cmake before writing the receiver build.
- **Symptom:** the core smoke probe links but fails with `Failed to load channel rdpdr`.
  **Cause:** the first probe used the low-level context constructor and inherited RDP8 network/device defaults outside the declared four-channel build.
  **Fix:** use `freerdp_client_context_new` to register the static addin provider, then explicitly select graphics/display/clipboard and disable unsupported network/device/audio channel settings in the probe before loading addins.
  **How found:** the container lifecycle failure and the pinned client/common/client.c plus cmdline.c; the corrected probe passes without a server or any network access.
  This is the build probe's configuration, not a claim that the receiver's connection policy is finished.

The build also checks generated FFmpeg definitions for H.264/HEVC and disabled GPL/nonfree code, and on iPhone requires both VideoToolbox hardware accelerators and FreeRDP's VideoToolbox definition.
An accepted configure flag alone does not establish that the requested backend was compiled.


### Core hosted probe-path failure

[Run 44692772893](https://github.com/Sparky-OS/flat-headset/actions/runs/44692772893), read 2026-11-20, used `ImageOS=macos26`, image `20261117.0516.1`, Xcode 26.6 build 17F113 and iPhoneOS SDK 26.5.
It compiled and installed OpenSSL, FFmpeg and FreeRDP for the iPhone, and linked `core-link-check.app/core-link-check`.
It then failed because lipo was given the nonexistent unbundled path.
The app job remained green; no core artifact was uploaded by this run.

- **Symptom:** lipo cannot open `freerdp/core-link-check` after a successful compile and install.
  **Cause:** [CMake defaults MACOSX_BUNDLE to ON for iOS](https://cmake.org/cmake/help/latest/variable/CMAKE_MACOSX_BUNDLE.html), so the executable is inside an application bundle.
  **Fix:** generate the exact executable path with [`$<TARGET_FILE:core-link-check>`](https://cmake.org/cmake/help/latest/manual/cmake-generator-expressions.7.html#genex:TARGET_FILE), verify that file exists and copy it to the build root's `core-link-check`.
  Use that same normalized file for lipo, otool and artifact packaging; do not guess the platform's bundle layout or remove a signature to pass the check.
  **How found:** the run's `[352/353] Linking C executable core-link-check.app/core-link-check` followed by the failing lipo path.
- **Symptom:** `Found FFmpeg ... found components: AVCODEC` is immediately followed by `FFmpeg AVCODEC not found - MJPEG support disabled in video codec wrappers`.
  **Cause:** pinned FreeRDP's `libfreerdp/CMakeLists.txt:179` tests `FFmpeg_avcodec_FOUND`, but `cmake/FindFFmpeg.cmake` sets `FFmpeg_AVCODEC_FOUND` with uppercase component names.
  **Fix for diagnosis:** check the independent H.264 path, generated definitions and actual libraries before treating this message as a lost decoder; do not force a variable or suppress the message to make the log green.
  **How found:** this run found the target prefix's libavcodec/libavutil, printed WITH_VIDEO_FFMPEG and WITH_VIDEOTOOLBOX, compiled `h264_ffmpeg.c.o` and linked the probe with the static codec libraries.
  The video-only FFmpeg configuration enables H.264 and HEVC, not MJPEG; no MJPEG decoder claim follows from finding avcodec.
  The optional wrapper diagnostic does not unset the explicitly enabled WITH_FFMPEG or WITH_VIDEO_FFMPEG in this build.

The probe links FreeRDP's build-tree static targets, and installed OpenSSL/FFmpeg archives.
It is not a separate consumer of the installed FreeRDP CMake/pkg-config package.
The artifact uses the installed FreeRDP archives; an independently configured installed consumer has not been tested.
Do not assume a byte-for-byte archive comparison is valid across installation: CMake's Darwin install script reruns ranlib on the installed static archive, as a generation-only Linux fixture confirms.
That fixture establishes CMake output layout and install commands, not an Apple linker or SDK build.
The runner also reports that CMake cannot find pkg-config under the ignored Homebrew prefix; its direct header/library lookup nevertheless finds the target dependencies, as the paths in the log establish.
Hardware decode and presentation remain unverified, and the corrected path/signature/archive checks still need a new hosted run.

The correction passes a fresh Linux build and client/channel/H.264 lifecycle test, a CMake-generated Darwin bundle-path fixture without an SDK, and the real packaging commands against a host artifact.
The original shell fails the log-derived bundle-path fixture; the corrected shell passes bundled and plain paths (including spaces) and still rejects a missing executable.
Stand-ins for lipo and otool in that fixture establish shell control flow only.
