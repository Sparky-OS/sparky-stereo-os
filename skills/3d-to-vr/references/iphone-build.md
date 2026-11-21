# Building Flat Headset for iPhone from Linux

**For the contributor: write and test portable code on Linux, compile the native application on a standard hosted macOS runner, then sign and install with Xcode on a Mac.**
Check freshness first: Intel runner inventory and Apple Xcode compatibility checked 2026-11-21; Intel KDE Connect, Cardboard and core archives passed run 44848751393; the Intel receiver awaits a rerun after installing the missing Metal component.
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
   Select the recorded Xcode installation explicitly for each runner, with no SDK download to the Linux station.
4. Compile the native arm64 app with the literal command below, `CODE_SIGNING_ALLOWED=NO` and no development team.
   A workflow must not contain credentials, certificates, provisioning profiles or an Apple account.
5. Package the built application under `Payload/FlatHeadset.app` as `FlatHeadset-unsigned.ipa` and keep its SHA-256 and receiver manifest entry in the same artifact.
   This is a development build artifact, not an installable signed application or a store submission.
6. Read the run for the exact pushed commit; a local lint pass, an absent run or a run for another SHA is not a hosted build result.
   Fix a failing run before starting the next program; three failures at the same step with no cause found are a stop to report.
7. Signing and installation now use Xcode on the person's Mac, with their free Personal Team added by them in Xcode settings.
   The Linux signing audit remains historical evidence.
   The session instructions and renewal helpers are being revised for this route; do not follow the former Linux sign-in procedure.
   Complete the unsigned Intel build checks before the one hardware session.

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
  FH_CORE_PREFIX="$RUNNER_TEMP/flat-headset-core/install" \
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
The macos-15 job runs the portable picture/catalog checks.
Once the app links OpenSSL, its native build follows the dependency build in the macos-26 job and takes `FH_CORE_PREFIX` from that build's install directory.
The core target includes client-common, TLS/authentication, FFmpeg H.264/HEVC and drdynvc/rdpgfx/disp/cliprdr channels.
Its link probe pulls in context creation, channel registration, H.264 lifecycle and OpenSSL/FFmpeg symbols.
The Linux `host` mode builds the same pinned dependencies and executes that probe without network access; the iPhone mode links it and checks arm64 and absence of a signature, without executing on a phone.
Only the iPhone mode compiles the VideoToolbox path; hardware decoding, software fallback behavior and zero-copy remain separate receiver tests.

The `FlatHeadset-core-arm64-COMMIT` artifact is a development archive of third-party headers/static libraries, licenses, source lock, build commit/configuration and the unsigned link probe.
It is not an IPA and must never be added to the renewal manifest.
The first core hosted run compiled and linked successfully but stopped at the probe-path check.
With the path taken from CMake, [run 44694434857](https://github.com/Sparky-OS/flat-headset/actions/runs/44694434857) passes both jobs for commit 3623f88 and uploads the core archive.
That archive was checked on Linux: its checksum, the three licence texts, no file of Apple's SDK inside, every object of the eight static libraries built for arm64, and the link probe an unsigned arm64 program for iOS 16.0 and later (SDK 26.5).
That first archive also holds OpenSSL's `legacy.dylib` provider module.
The next configuration disables the module at build time with `no-module no-legacy`, rather than deleting an installed dependency after packaging; see the provider trap below.
Nothing was run on a phone.
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
Hardware decode and presentation remain unverified.
Run 44694434857 establishes the corrected path/signature/archive checks; the provider-removal and foreground-pairing changes are established by run 44698940422 below.

The correction passes a fresh Linux build and client/channel/H.264 lifecycle test, a CMake-generated Darwin bundle-path fixture without an SDK, and the real packaging commands against a host artifact.
The original shell fails the log-derived bundle-path fixture; the corrected shell passes bundled and plain paths (including spaces) and still rejects a missing executable.
Stand-ins for lipo and otool in that fixture establish shell control flow only.


## Static provider and foreground pairing integration

The downloaded core from commit 3623f88 has SHA-256 `249abac088171376e189d7f7b4f8fffdfac8c74870179aa428a37ad9f8e87b6b`.
Its 648 members include eight static libraries, the three dependency licenses and an unsigned arm64 link probe for iOS 16.0 / SDK 26.5.
Every Mach-O object in those libraries was checked as arm64; no SDK headers or frameworks are in the archive.
This is a build artifact audit, not runtime proof.

- **Symptom:** a supposedly static iPhone core archive contains `lib/ossl-modules/legacy.dylib`.
  **Cause:** OpenSSL's `no-shared` does not disable provider modules.
  **Fix:** configure the pinned OpenSSL with `no-shared no-module no-legacy`; reject remaining `.dylib` or `.so` inputs before packaging.
  [OpenSSL's own build options](https://github.com/openssl/openssl/blob/openssl-4.0.1/INSTALL.md) distinguish shared libraries, modules and the legacy provider.
  Keep FreeRDP's `WITH_INTERNAL_MD4`, `WITH_INTERNAL_MD5` and `WITH_INTERNAL_RC4` enabled.
  **How found:** inspection of the green hosted core artifact; a fresh Linux analogue produces no provider module and passes MD4, MD5, HMAC-MD5 and RC4 known answers plus the pinned upstream `TestSspiNTLM` exchanges using in-memory public fixtures.
  The checked iPhone artifact from run 44698940422 contains no loadable provider.
- **Symptom:** WinPR prints `OpenSSL LEGACY provider failed to load, no md4 support available!` even with internal MD4 enabled.
  **Cause:** `winpr/libwinpr/utils/ssl.c` attempts the provider and emits the warning unconditionally for OpenSSL 3 and later.
  **Fix for diagnosis:** execute the configured WinPR MD4 and NTLM paths, check the provider remains unavailable, and report the warning separately from their result.
  Do not suppress the warning or enable a module merely to make it disappear.
  **How found:** the configured host build passes its crypto known answers and upstream NTLM exchanges after normal `winpr_InitializeSSL`, with the warning retained.
  This does not establish a live KRdp login or arbitrary legacy protocols.
- **Symptom:** new C++ pairing code fails against OpenSSL 4 on `X509_NAME_add_entry_by_txt` and a deprecated `X509_cmp_current_time`.
  **Cause:** `X509_get_subject_name` now exposes a const name; the old time helper is deprecated.
  **Fix:** build an owned `X509_NAME`, set it with `X509_set_subject_name`, and compare validity with `ASN1_TIME_cmp_time_t`.
  Accept only its documented -1/0/1 results as appropriate; -2 means invalid time, not an earlier date.
  **How found:** the Linux build with the exact pinned OpenSSL headers and warnings treated as errors.

The foreground-pairing target adds a Computers screen, before RDP integration.
Its discovery uses the desktop's `_kdeconnect._udp` Bonjour service, whose SRV value advertises the TCP port.
The desktop implementation is [Avahi discovery](https://github.com/Sparky-OS/kdeconnect-kde/blob/master/core/backends/lan/avahidiscovery.cpp); the remaining identity exchange occurs after mutual TLS in protocol 8.
Declare that specific service in `NSBonjourServices` and provide the ten-language `NSLocalNetworkUsageDescription`.
[Apple TN3179](https://developer.apple.com/documentation/technotes/tn3179-understanding-local-network-privacy) distinguishes ordinary Bonjour/local-network permission from restricted multicast operations.
Do not replace this with an arbitrary UDP broadcast or assume permission was granted because compilation succeeded.

Follow the Android `LanLinkProvider.java`, `PairingHandler.kt` and `SslHelper.kt` in the receiver tree.
The TCP initiator is the TLS server.
Check the device ID in the peer certificate and the encrypted identity, require protocol 8, and reject a changed saved certificate pin.
For first pairing, show the same timestamped public-key verification code and require local confirmation as well as remote acceptance before saving trust.
Store the identity and pins in this app's Keychain; no private identity is passed to a separate app through a URL or an unverified shared entitlement.
Stop connections and pending prompts when the screen closes or the app enters the background.
The current tests use AF_UNIX socketpairs inside a container with no network; they cover mutual TLS, pin reuse/change, identity mismatch, downgrade refusal, confirmation ordering, timeouts and malformed packets.
They establish the portable code only.
Native Bonjour, Keychain behavior and interoperability with a desktop remain device checks after the hosted compile.
The pairing-only target did not consume plugin traffic or desktop credentials.
The next integration adds the paired RDP lifecycle described below, followed by decode to Metal and the actual Android viewer mathematics.


## Paired RDP session lifecycle

**For receiver contributors:** preserve authorization from the paired identity through session creation, TLS and teardown.
Checked against the pinned FreeRDP 3.28.0 source and the Android/desktop virtualmonitor implementations on 2026-11-20.

[Run 44698940422](https://github.com/Sparky-OS/flat-headset/actions/runs/44698940422) compiled the foreground pairing target and static core successfully.
The downloaded app has SHA-256 `1367bca24581b9daaf495037f61d07ce4234e0aeaa3d595f80d32d6caa5a79a1`.
The core has SHA-256 `7f9823119cb6f00d8497fe907a147d08aea50a1581d3dc602f5c7e5a166d18e7`, 647 members, eight static libraries and no `.dylib` or `.so` provider.
Every archive Mach-O object is arm64; the core probe and app are unsigned arm64 iOS executables with minimum 16.0 and SDK 26.5.
The app links UIKit, Security, Metal/MetalKit and system Foundation/C/C++ libraries; it does not yet link the FreeRDP session adapter in this checked run.
These are downloaded-artifact and compile checks, not phone behavior.

1. Save the verified pairing pin before enabling Catch or accepting session replies.
   Bind the controller to the peer ID, its certificate pin, the local certificate fingerprint and `getpeername`'s numeric address from the authenticated socket.
2. Advertise both virtualmonitor packet types in the encrypted identity.
   Exchange capabilities only after pairing, require protocol 2 and native-panel version 1, and send a fresh session ID with the physical panel descriptor.
   The descriptor's identity is the local certificate SHA-256, which the desktop compares with its paired phone certificate before asking for session permission.
3. Accept credentials only in a matching `connect` reply with the same panel, NLA security and SHA-256 certificate fingerprint.
   Ignore stale/replayed session IDs; refuse malformed fields, mismatched addresses and security downgrades.
   Receive the RDP address from the authenticated control socket rather than accepting a remote `host` field.
4. Create the context through `freerdp_client_context_new`, which registers static channel addins.
   Keep `rdpClientContext` first in the extended context so the common graphics channel handlers see the expected layout.
   Set `ExternalCertificateManagement`, install `VerifyX509Certificate`, and return 2 only for the exact session fingerprint, host and port; return 0 otherwise.
   Refuse gateway/redirect verification, set the Redirect callback to reject, and disable auto-reconnect and weaker security protocols.
5. Load the declared channels in PreConnect, initialize GDI in PostConnect, and publish connected only after `freerdp_connect` succeeds.
   Check the negotiated native dimensions, service event handles, then disconnect, unsubscribe channels, free GDI and free the context after the worker ends.
   Stop or unpair revokes the grant; a new Catch creates a fresh grant and context.
6. Test the control parser and the certificate callback on Linux with the pinned static libraries before the native compile.
   The host build adds `paired-session` to the lifecycle, pairing and NTLM tests.
   Then push through the reviewed workflow and check the unsigned app's new dependency closure; the session adapter's native compile and installed-library consumer link passed run 44702615908 below.

The compiled session adapter initializes a BGRA GDI surface; the next integration presents its completed paints to Metal, followed by viewer mathematics.
No received desktop, VideoToolbox runtime, optical result or real-phone lifecycle has been established.
Native status messages cover refusal, invalid replies, certificate mismatch, timeout, stop and reconnect in all ten catalogs.
Remote error text is not a translated status and is not passed directly to the screen.

- **Symptom:** a reply received after timeout can still create an RDP grant.
  **Cause:** clearing the deadline alone leaves the matching session ID eligible for a later `connect` reply.
  **Fix:** accept a first grant only while waiting for permission/start/connect information, and invalidate every outstanding grant on timeout or revoke.
  **How found:** the negative `paired-session` test failed on the late reply, then passed after the state restriction; a fresh request receives a new nonce.
- **Symptom:** certificate pinning code can be skipped for an otherwise trusted RDP certificate.
  **Cause:** the pinned FreeRDP TLS implementation's normal CA path can return before the interactive certificate callbacks.
  **Fix:** use `ExternalCertificateManagement` with `VerifyX509Certificate`, including host/port and session-revocation checks, instead of relying only on `VerifyCertificateEx`.
  **How found:** reading `libfreerdp/crypto/tls.c` at the pinned revision and exercising the adapter's actual verification entry point with matching, changed, redirected and revoked fixture certificates.
  This callback test does not establish a live TLS/NLA exchange.
- **Symptom:** a retry is canceled immediately by the previous session's failure state.
  **Cause:** the control loop keeps polling a stopped adapter after sending Stop.
  **Fix:** move the old adapter out of the active slot, abort it and join its worker before accepting a new session grant.
  **How found:** review of the native control loop before hosted compilation; foreground runtime behavior still needs the device check.

The app now names all eight installed static archives explicitly and includes the FreeRDP and FFmpeg licenses alongside the existing licenses.
The framework list comes from the checked core probe's load commands: Foundation, CoreFoundation, VideoToolbox, CoreMedia and CoreVideo, plus the app's UIKit, Security and Metal frameworks.
Do not blindly copy the installed `.pc` private requirements: this pinned FreeRDP package still lists unbuilt libavfilter/libavformat and WinPR's platform-independent `-lrt` despite this successful iOS closure.
Run 44702615908 establishes that separate installed-library consumer link.


## Completed GDI paints to Metal

[Run 44702615908](https://github.com/Sparky-OS/flat-headset/actions/runs/44702615908), checked on 2026-11-20, passes both jobs for receiver commit df8455ea6e74541d53651379074938227368774f.
The downloaded app checksum is `dde15f79829a4f32cacd848747f6430e23e4d5394761b4d43ea4ce9ae871cd94`; the core checksum is `8f910f5b48b3628511cab5333bf18966cc9a07c96a42d37fc0b4fda94953c018`.
The app now links the installed FreeRDP/FFmpeg core, includes all five license files, and has no embedded framework or dylib.
The core has eight static libraries, all Mach-O objects arm64, and no loose provider module.
Both executables are unsigned arm64 for iOS 16.0 and later, built with SDK 26.5.
This proves native compilation and packaging of the paired session, not a desktop arriving on a phone.

For the decoded-frame integration, keep the paired grant as the authorization boundary.
Attach BeginPaint/EndPaint after GDI initialization and preserve FreeRDP's graphics channel handlers.
Reset both the aggregate dirty flag and the dirty-region count at the start of each paint.
Copy a completed BGRA surface into owned rows before the decoder can change it again.
Keep one pending frame, replacing only that pending frame when the consumer is late.
Retain immutable textures for in-flight GPU commands, bound those commands and consume the latest frame only when a GPU slot is available.
Check the received native extent against the drawable and read matching texels; this step must not add eye scaling or separation.
Closing the session closes the queue and hides the old image; a first-frame timeout and renderer errors must be visible in every language.
Pushing the desktop controller must preserve the authenticated Computers connection; leaving or backgrounding the receiver still closes it.

This path is VideoToolbox through FFmpeg, CPU transfer and GDI reconstruction, owned BGRA memory, then a Metal texture upload.
It is not a zero-copy CVPixelBuffer-to-Metal path.
The session advertises H.264; compiled HEVC support is not evidence of HEVC negotiation.
The frame queue tests cover padded rows, complete left/right geometry, ownership, late-frame replacement, concurrent coherence and closed/malformed inputs.
The GDI integration test allocates the actual pinned FreeRDP surface, runs the production paint handoff and checks forty pairs, dirty-region reset, empty paints, wrong extents and closure without a network connection.
These checks do not exercise an encoded stream, Apple's decoder, the Metal shader or the optics.
The view and original strict patch passed run 44770385750 below; the later authorized phone session is still needed for runtime evidence.
The Android viewer's actual profile mathematics follows this integration; no distortion coefficient is inferred here.

- **Symptom:** a failed VideoToolbox device initialization logs a software fallback and still attempts decoding.
  **Cause:** pinned FreeRDP's `h264_ffmpeg.c` jumps past the hardware setup to the common codec-open call; its frame receive path also accepts a non-hardware frame.
  **Fix:** stop presenting and ask for a per-session software-decoding choice, as described below.
  The initial patch instead ended the session; that removed the silent switch but incorrectly removed the person's choice.
  Keep the patch beside the source lock in the core artifact; apply it with an exact forward or reverse check, never ignore a failed hunk.
  **How found:** source review of 3.28.0 and the current default branch before wiring the presentation path.
  The Linux analogue checks both failure reasons and decisions through the core permission API; Apple-path compilation and an actual hardware failure remain separate checks.
- **Symptom:** a GDI receiver accumulates dirty-region entries although it copies the complete surface each time.
  **Cause:** clearing only `invalid->null` leaves `hwnd->ninvalid` growing in `gdi_InvalidateRegion`.
  **Fix:** reset the count with the aggregate dirty flag in BeginPaint, as the pinned SDL client does.
  **How found:** reading the pinned region allocator and SDL paint callback, then checking the reset across forty real GDI paints.
- **Symptom:** an asynchronous renderer can show mixed frames or an increasing delay.
  **Cause:** it references decoder-owned mutable pixels, or appends each frame to an unbounded main-thread/GPU queue.
  **Fix:** copy into owned complete frames, keep only the latest pending one and retain immutable textures for at most two GPU submissions.
  **How found:** review of decoder/renderer ownership and a concurrent producer/consumer fixture; actual phone cadence and latency remain unmeasured.

[Run 44770385750](https://github.com/Sparky-OS/flat-headset/actions/runs/44770385750) passes both jobs for commit 4970452: the desktop view, its Metal fragment and the core with the strict VideoToolbox patch compile and link, and the unsigned package was checked on Linux (arm64, no signature, no embedded library).
No frame has been decoded or shown on a phone.


## Hardware failure offers an explicit session choice

When VideoToolbox cannot initialize or yields another frame format, hide the desktop and say that hardware video decoding failed.
Offer two actions in the person's language: continue with software decoding for this session, with the explicit warning that it is slower and uses more battery, or go back.
Never interpret a timeout, remote packet, stored pairing or closing the prompt as permission.
No design found for remembering the decoder choice across sessions; every new paired RDP session starts with hardware decoding.

The receiver's patch retains its `0001-require-videotoolbox.patch` filename but now carries a per-decoder permission callback.
GDI passes the session callback into both AVC420 and AVC444 contexts before initialization.
The callback's query operation does not block or prompt; it reports only an existing software choice for that session.
The two failure reasons pause the owned-frame queue and wait on a cancellable condition variable while the main thread shows the actions.
Continue permits the software path in that context and subsequent surfaces of the same session.
Go back, Stop, backgrounding and losing the paired control connection cancel the waiter before FreeRDP teardown.
There is no process-global flag, environment variable or stored preference.
Keep the authenticated connection while the person decides and hold only its connection deadline during that decision.
A later failure is still a failure, not another automatic switch.

For initialization failure, approval skips the hardware setup before opening FFmpeg's decoder.
For hardware format negotiation failure, select an offered YUV420P or YUVJ420P software format only after approval.
For a received software frame, take an owned reference to those planar pixels only after approval; do not interpret an unrelated format as those planes.
Clear the renderer's old texture and invalidate older GPU completion callbacks before resuming, so a completed old submission cannot hide the waiting message or make a stale frame look new.
An early failure can happen before the desktop view's first draw: its layout path must also present the choice.

The Linux analogue uses the real core permission API to inject each failure reason, tests both actions, verifies that no pending frame survives the wait, and decodes an authored H.264 left-red/right-blue pair after approval.
It tests cancellation and new sessions separately; a new session must answer the software query with false.
These tests do not simulate Apple's VideoToolbox device creation or execute UIKit.
Run [44779150423](https://github.com/Sparky-OS/flat-headset/actions/runs/44779150423) compiled and uploaded the updated core for 576dd93.
The application compile then stopped at an invalid Objective-C instance-variable initializer; the correction then passed both jobs in [run 44783586937](https://github.com/Sparky-OS/flat-headset/actions/runs/44783586937) for cd3c5f5. Its downloaded IPA and core passed checksum, arm64, iOS 16.0, unsigned and no-embedded-dylib checks. A device check still remains.

- **Symptom:** the software decoder's eye-color assertion fails although decoding completes.
  **Cause:** the first generated fixture used FFmpeg's limited-range BT.601 color source directly, but the RDP conversion uses full-range BT.709.
  **Fix:** explicitly convert and mark the fixture as full-range BT.709 before encoding; keep the same pixel assertions.
  **How found:** the initial Linux analogue failed, then the corrected fixture passed every pixel in both eyes through the pinned FreeRDP/FFmpeg decoder.
  This qualifies the authored SDR fixture, not arbitrary HDR or color metadata.
- **Symptom:** the receiver reports a generic disconnection after a hardware failure even though software decoding could continue.
  **Cause:** replacing an automatic fallback with an unconditional error removed both the silent switch and the explicit alternative.
  **Fix:** pause presentation, explain the hardware failure and wait for the person's session-scoped choice; cancel that wait on teardown.
  **How found:** review of the original strict patch against the explicit-choice rule, followed by both-decision tests through the actual permission callback API.

- **Symptom:** Clang stops at `Desktop.mm:18:34` with `expected ';' at end of declaration list`.
  **Cause:** `_presentationEpoch=0` used a C++ member initializer inside an Objective-C instance-variable block.
  The C++ `shared_ptr` and clock members are valid there; the scalar initializer syntax is not.
  **Fix:** declare `_presentationEpoch;`; Objective-C allocation already zeroes scalar instance variables.
  Assign any nonzero initial value inside the initializer method.
  **How found:** the complete failing native build step identifies this sole error; Linux Clang reproduces it with authored test doubles and parses both corrected controller files.
  Run `bash ios/Tools/check_objc_syntax.sh` locally to check `Main.mm`, `Desktop.mm`, `Desktop.h`, `Computers.mm` and `ViewerSettings.mm` with C++17, ARC, blocks and warnings as errors.
  Its minimal declarations come from our call sites, not Apple's files; they check syntax and local type consistency, not real SDK signatures, ABI, availability, linking, shader compilation or runtime behavior.
  Keep those test includes out of every product build and keep the hosted Xcode compile as the SDK check.


## Carry the Android viewer geometry across unchanged

Use the existing Android `FittedLensCorrection.kt`, `headset_fitted.frag`, `PanelView.kt` and `PanelDescriptor.kt` in [Flat Headset](https://github.com/Sparky-OS/flat-headset), not coefficients inferred from a viewer's brand.
Uncorrected remains the default. The other independent choices are the existing Shinecon fitted D mapping and a Cardboard QR profile; never compose them.
The fit uses strength 0.13 from the existing Android implementation, and was checked for one Android phone placement in the adjustable viewer. That is not an optical proof for an iPhone.
The iPhone selection explains that limitation, is saved like Android's viewer selection, and is captured before establishing the paired connection. Decoder consent remains separate and per session.

For QR geometry, retain the portable C++ subset from [Cardboard 8bd424da](https://github.com/googlevr/cardboard/tree/8bd424da7f1e399255a1b6e7c02be8e281ecc974): lens distortion, radial inverse, mesh and matrix, with its license and original source hashes.
Feed validated actual DeviceParams and physical screen dimensions into its constructor. Do not substitute a fit strength for the QR distortion polynomial.
The receiver uses the exact Cardboard v1 bytes only when v1 is explicitly chosen; an imported full profile link is decoded locally and invalid data is refused.
Short-link resolution and the separate Cardboard program's scanner are not implemented by that import field.
Use the upstream iPhone DPI table for the screen model; refuse unknown physical dimensions rather than choosing a plausible DPI.
Preserve the upstream border constant, FOV and viewport math; retain its 1600 vertices and 3158 strip indices per eye.
For Metal, flip mesh V exactly as the upstream Metal renderer does; keep the whole-panel viewport and each eye's source region.
Never resize each eye to fill a lens mask or change separation to hide black edges.
The authenticated native-panel reply must echo the selected Android lens-profile ID along with the exact panel dimensions and identity.

Local commands, in the isolated Linux test environment:

```sh
bash ios/Tools/check_objc_syntax.sh
python3 ios/Tools/check_localizations.py
cmake -S ios -B build/viewer -DCMAKE_BUILD_TYPE=Debug -DFH_VIEWER_GLES_TEST=ON -DFH_VIEWER_SESSION_TEST=ON
cmake --build build/viewer --parallel 4
ctest --test-dir build/viewer -V
```

EGL/GLES2 and OpenSSL development packages are needed for these two optional tests; ordinary portable CMake checks also run on the hosted Mac.
The expanded authored Objective-C stand-ins cover the profile settings UI and Metal mesh submission, without including Apple's headers.
The 51 native string keys include the profile choices and refusals in ten languages.
The native viewer changes passed both jobs in [run 44787732216](https://github.com/Sparky-OS/flat-headset/actions/runs/44787732216) for 159bc572.
The downloaded IPA passes checksum, unsigned arm64, iOS 16.0, no embedded dynamic library and six-license checks.
All optical checks on a phone remain unproven.

- **Symptom:** a port's fitted picture differs by half a pixel or appears to use a different strength.
  **Cause:** removing one of Android's two half-pixel operations, treating the fit strength as a QR coefficient, or measuring the radius in different units changes the mapping.
  **Fix:** share the exact scalar pixel mapping between portable C++ and Metal and compare it against Android's actual shader on headless GLES. Keep its integer centre and per-eye diagonal normalization.
  **How found:** the 0.13 mapping passes every pixel at 1920x1080, 2340x1080 and 1280x720 in both vertical orientations, with at most one channel value of interpolation rounding; bypass is exact. A deliberately wrong coefficient produces mismatches.
- **Symptom:** a plausible QR mesh is not demonstrably the same geometry as Android's.
  **Cause:** testing only a reimplementation against itself misses parser, FOV, viewport and eye-order changes.
  **Fix:** build the pinned, unmodified Cardboard sources with their generated protobuf parser as an independent oracle, and compare every mesh coordinate, UV and index after the documented Metal V flip.
  **How found:** the actual Cardboard v1 and I/O 2015 profiles give byte-identical 3200 vertices/UVs and 6316 indices at all three test panel sizes; exchanging the eyes fails the comparison.
- **Symptom:** a malformed imported profile could hang inverse-distortion construction.
  **Cause:** upstream's secant inverse loop has no iteration bound.
  **Fix:** bound parsing and inverse iterations, refuse nonfinite results and report the invalid profile in the person's language. Do not silently replace its coefficients or select v1.
  **How found:** source inspection while accepting imported profile bytes; legitimate-profile oracle comparisons and malformed-input tests preserve the valid math.

These are arithmetic, parsing and session-control proofs on Linux. They do not execute Metal, display an RDP desktop on a phone or verify lens alignment through a viewer.


## KDE Connect as a separate unsigned application

The KDE Connect iOS base is [a3036396](https://invent.kde.org/network/kdeconnect-ios/-/tree/a303639652c1cf486bd6fb61335970723c2085a7).
The `kdeconnect-iphone` job in Flat Headset's unsigned workflow checks out Sparky-OS/kdeconnect-ios at an exact commit and runs its `Sparky/build_unsigned.sh` and `Sparky/package_unsigned.sh` scripts.
It emits a separate `KDEConnect-unsigned-COMMIT` artifact with the IPA, SHA256SUMS and the `kdeconnect` renewal-manifest role.
The native job passed with KDE Connect `0e2b712987e3a347af3f8a8f5103b981935ed30c` in [the green hosted run](https://github.com/Sparky-OS/flat-headset/actions/runs/44795627406).
The image reported macos26 20261117.0516.1, Xcode 26.6 and iPhoneOS 26.5.
The downloaded IPA independently passed its SHA-256 check: one unsigned arm64 executable, iOS 16.0 minimum, the expected bundle identity, ten VirtualMonitor catalogs and no embedded framework, dylib or provisioning profile.
This proves compilation and packaging; Security identity import, Bonjour and Keychain persistence still require the phone.

KDE Connect owns the sole pairing identity and trust; the receiver reads them through the shared keychain group.
Xcode signing must grant the receiver access to that group under the same Personal Team before a hardware session.
KDE Connect's virtualmonitor plugin checks the paired computer's protocol-v2 capabilities, explains refusal or timeout in ten languages, and opens only `flatheadset://catch`.
That URL carries no address, pin, password or session credential and never authorizes a connection.
Flat Headset opens its computer list, confirms its own pairing with the same PC and owns the virtual monitor and RDP session while in the foreground.
Returning to the KDE Connect page performs a fresh capability query; losing pairing or reachability revokes the launch permission.
Do not advertise this KDE Connect app as an RDP consumer or pass the receiver credentials through a URL.

Local checks in an isolated Linux container with Clang, GNUstep Base development files, GCC, Make and Python:

```sh
bash Sparky/test_protocol.sh build/protocol
python3 Sparky/Tests/PackageTest.py
# Fetch and hash-check the source before the test container loses network access.
python3 Sparky/fetch_openssl.py sources
bash Sparky/build_openssl.sh host sources/openssl build/openssl
cc -Wall -Wextra -Werror -I build/openssl/install/include Sparky/Tests/CryptoTest.c build/openssl/install/lib/libcrypto.a -ldl -pthread -o build/crypto-test
OPENSSL_MODULES=/nonexistent OPENSSL_CONF=/nonexistent build/crypto-test
```

The Objective-C protocol implementation runs against GNUstep Foundation; its tests cover trust gates, malformed replies, revocation, deadline/retry, unsolicited credentials and exact certificate equality.
The receiver's separate Linux mutual-TLS tests run over local socket pairs without a container network.
The package fixtures test rejection of extra apps, signatures, profiles, frameworks, dynamic libraries, extensions, Watch bundles, missing catalogs and wrong bundle identity.
They do not replace the hosted lipo/codesign checks or a later downloaded-IPA audit.
The twelve added UI keys have all ten native catalogs; upstream strings remain in their own catalog.
Wait for all three unsigned applications before one device session for signing, installation and observations.

- **Symptom:** an independently signed KDE Connect build searches KDE's team Keychain group for its UUID.
  **Cause:** `KdeConnectSettings.getUUID` names a group belonging to the upstream signing team.
  **Fix:** use the app's own default Keychain group and an app-specific UUID service; do not assert shared credentials with Flat Headset.
  **How found:** source inspection of the pinned upstream, including its previously merged Keychain fixes; on-device persistence remains unproven.
- **Symptom:** the OpenSSL Swift package supplies an embedded dynamic framework to a build intended to contain a single unsigned executable.
  **Cause:** the pinned package is a binary target; its arm64 Mach-O header has file type 6, `MH_DYLIB`.
  **Fix:** replace that package with hash-checked OpenSSL source and static archives; reject dynamic libraries in the IPA.
  KDE Connect's iOS 16/17 identity import needs the legacy provider, unlike FreeRDP's core.
  Configure this separate build with `no-shared no-module` and retain legacy as a built-in provider, as [OpenSSL's provider build rules](https://github.com/openssl/openssl/blob/openssl-4.0.1/providers/build.info) specify.
  **How found:** inspected the package manifest and binary header, then built OpenSSL on Linux and round-tripped both PKCS12 formats with nonexistent module/config paths.
  Apple's identity import is still a device check.
- **Symptom:** OpenSSL 4 rejects a mutable `X509_NAME *` from `X509_get_subject_name` under warnings as errors.
  **Cause:** the accessor returns a const pointer.
  **Fix:** construct an `X509_NAME`, assign it with the subject and issuer setters, then free the temporary name.
  **How found:** the static-library identity-format test caught the incompatible declaration; the updated helper and test preserve the certificate fields.
- **Symptom:** an unsigned build still executes a package build plugin despite `-skipPackagePluginValidation`.
  **Cause:** that flag suppresses validation, not execution; upstream's CI comment claims otherwise.
  **Fix:** the unsigned fork removes its SwiftLint target dependency and unused package references, keeping only the three linked source packages pinned by revision.
  **How found:** inspection of the project dependency graph and upstream CI command, then parsing every project reference and checking the exact package lock on Linux; the hosted run also resolved and built the pinned packages successfully.


## Cardboard camera profile application

The separate `cardboard-iphone` job checks out Sparky-OS/cardboard at an exact commit and the matching Flat Headset workflow commit in sibling folders.
Its base is Google's [Cardboard 8bd424da](https://github.com/googlevr/cardboard/tree/8bd424da7f1e399255a1b6e7c02be8e281ecc974).
The native AVFoundation capture path is adapted from `sdk/qrcode/ios/qr_scan_view_controller.mm`; no Android source is changed.
The new `profile-ios` target links the receiver's actual profile parser and Cardboard C++ sources, so both programs validate the same parameters.
It adds no lens coefficient or output-format selector.
The application carries GPL-3.0-or-later terms for the shared receiver code and preserves Google's Apache-2.0 notices and licence.

The workflow calls `bash cardboard/profile-ios/Tools/build_unsigned.sh "$RUNNER_TEMP/cardboard-iphone"` and its packaging script.
It retains `Cardboard-unsigned-COMMIT`, containing an unsigned IPA, SHA256SUMS and `cardboard-artifact.json` with both source commits and the `cardboard` renewal role.
The build uses UIKit, AVFoundation, Foundation and QuartzCore from the hosted SDK only, iOS 16.0 minimum, arm64 and no signing team.
This new target awaits its first hosted build; Linux syntax doubles do not qualify Apple's APIs.

Full QR links are parsed offline.
The exact upstream `g.co/cardboard` code denotes Cardboard v1; an invalid scan never silently selects v1.
A shortened `goo.gl` or `g.co` link requires an explicit localized action before an ephemeral HTTPS HEAD request, with five redirects and 10/15-second request/resource limits.
Other hosts, credentials, ports, query/fragment additions to shortened links and excessive input are refused.
The final full profile is consumed locally without fetching its page or body.
Cancellation/backgrounding stops capture and requests; generation and capture-output checks reject stale callbacks.
Ten language catalogs cover all fifteen UI keys and three InfoPlist keys, including the camera usage sentence.

The **Use in Flat Headset** action passes only validated lens parameters through `flatheadset://viewer?p=BASE64URL`.
Flat Headset revalidates the bytes and screen geometry, then asks before saving the profile for its next connection.
The person's current frame stream is not reconfigured by a URL.
The receiver's full-link paste field stays available as the second way.
No credential crosses app boundaries and this profile handoff authorizes no desktop session.

Linux proof uses an isolated container without a network: the production policy tests permissions, bad profiles, consent, timeout/failure, redirect bounds, cancellation and stale callbacks.
Actual v1 and I/O 2015 parameter bytes and per-eye mesh coordinates survive the handoff unchanged.
An independent QR encoder/decoder checks both fixtures at four rotations and feeds the result into that same policy.
It does not execute AVFoundation or demonstrate focus, camera permission UI, URL routing or physical lens alignment.
Keep the five-file Objective-C++ syntax pass before every push; stand-ins remain test-only and ship in no app.
The package fixtures reject signature commands, embedded dynamic code, wrong identities and missing catalogs/licences; Xcode plus a downloaded IPA audit still settle the native artifact.

- **Symptom:** the upstream scanner has fixed English text, and denied camera access can lead into Settings without a clear choice.
  **Cause:** its camera UI predates this three-program route and its ten-language catalog.
  **Fix:** explicit permission state, a localized refusal and retry action, with no forced Settings jump or fallback viewer.
  **How found:** upstream [issue 384](https://github.com/googlevr/cardboard/issues/384), [issue 527](https://github.com/googlevr/cardboard/issues/527) and the pinned camera source; tested policy branches on Linux, native UI awaits the phone.
- **Symptom:** some QR parameters can freeze a consumer during lens construction.
  **Cause:** unvalidated profile data reaches the distortion routine, as reported in upstream [issue 182](https://github.com/googlevr/cardboard/issues/182).
  **Fix:** use the receiver's bounded parser and existing geometry validation at both ends; retain the real profile, never repair it by inventing coefficients.
  **How found:** upstream report, source inspection and existing malformed-profile/mesh tests; this does not claim reproduction of every upstream fixture.
- **Symptom:** an old camera or redirect callback changes a newer scan after cancellation.
  **Cause:** asynchronous capture and URL requests can outlive the visible scan.
  **Fix:** serialize camera start/stop, bind policy transitions to a generation, and reject callbacks from a different output/session.
  **How found:** lifecycle review and stale-generation Linux tests; actual background capture cancellation remains a phone observation.

Prepare all three packages using [the one-session page](iphone-session.md).
The manifest joiner checks their common workflow commit, exact roles/IDs and IPA hashes before writing the private renewal input.
It neither authenticates nor installs; the person types their account only at the later xtool authentication step.


## Intel macOS builds and Xcode 26

The unsigned workflow builds each complete program on both `macos-26` (arm64, Xcode 26.6) and `macos-15-intel` (x86_64, Xcode 26.3).
The selected `DEVELOPER_DIR` values are `/Applications/Xcode_26.6.app/Contents/Developer` and `/Applications/Xcode_26.3.app/Contents/Developer`.
The Intel runner's default Xcode is 16.4, so accepting the default would miss FreeRDP's Xcode 26 requirement.
[GitHub's macOS 15 inventory](https://github.com/actions/runner-images/blob/main/images/macos/macos-15-Readme.md) lists Xcode 26.0.1, 26.1.1, 26.2 and 26.3.
Its [macOS 26 Intel inventory](https://github.com/actions/runner-images/blob/main/images/macos/macos-26-Readme.md) also lists 26.4.1, 26.5 and 26.6.
The standard Intel label is `macos-15-intel`, not the larger-runner `macos-15-large` label.
Xcode 26.3 allows the Intel build to be reproduced from macOS Sequoia 15.6, without requiring Tahoe first.
[Apple's requirements](https://developer.apple.com/xcode/system-requirements) give Xcode 26.0 through 26.3 a Sequoia 15.6 floor; the listed 26.4.1 through 26.6 require Tahoe 26.2.
Both groups support connected iOS 16 devices; Xcode 27's connected-device support starts at iOS 17 even though its deployment-target column starts earlier.
Do not infer connected-device support from a deployment-target setting.

Each matrix job starts by printing the image name/version, `uname -m`, `xcodebuild -version` and `xcodebuild -showsdks`.
It refuses an unexpected host architecture or missing selected Xcode with a plain error.
The core job also records the selected Xcode installation's disk usage; that figure is neither the archive's download size nor a fixed space requirement for every installation.
Intel artifacts append `-intel` after the workflow commit, so parallel jobs cannot replace each other's IPA, core archive or checksum.
The artifact contents and all three app targets remain unsigned arm64 for iOS 16.0, regardless of the host CPU.
No account, development team, provisioning profile or signing key is available to these jobs.
The Intel receiver app remains unverified until the missing Metal component is installed and the rerun produces a checked IPA; the first run results are recorded below.

Host/target audit:

- OpenSSL's own `ios64-xcrun` target selects `xcrun -sdk iphoneos cc` and arm64; its assembly generators use host Perl, and apps/tests are disabled.
- FFmpeg's target compiler and flags use the iPhoneOS SDK and arm64. Its host compiler now explicitly uses `xcrun --sdk macosx --find clang`, with the macOS sysroot in host compile and link flags. Generated build-time programs must run on the Intel Mac, not on iOS.
- FreeRDP's CMake target is iOS/arm64. Include, library and package lookup are confined to the target prefix and SDK; program lookup stays on the host. Both `/usr/local` and `/opt/homebrew` are excluded as target dependency prefixes. Build tools come from the host PATH, without a hard-coded Homebrew path.
- KDE Connect's three Swift package dependencies remain revision-pinned source packages. Its OpenSSL archives are rebuilt on each runner. Its protocol executable is a macOS host test; the crypto link probe and app are iPhone targets.
- Cardboard builds the shared portable profile code as a host test, then builds its native program for the phone. No host-architecture prebuilt binary was introduced.

Traps found by source and runner-inventory inspection, before an Intel run:

- **Symptom:** FreeRDP rejects the default compiler on an Intel runner. **Cause:** the macOS 15 default is Xcode 16.4. **Fix:** select its installed Xcode 26.3 explicitly and fail if that installation disappears. **Found:** GitHub's Xcode inventory and FreeRDP's declared requirement.
- **Symptom:** a generated codec build tool targets the phone or picks a different host compiler through PATH. **Cause:** target and host compilers were not independently specified. **Fix:** FFmpeg gets a separate macOS compiler/sysroot for build-time tools. **Found:** FFmpeg n8.1 configure's host-compiler default and cross-compile options; this is preventive, not a claimed observed Intel failure.
- **Symptom:** parallel jobs contend for an artifact name. **Cause:** names used only the workflow commit. **Fix:** Intel job names append `-intel`. **Found:** reviewing the new matrix before upload.
- **Symptom:** the receiver cannot read KDE Connect's keychain after a local Xcode build. **Cause:** the former Linux signer injected the shared entitlement; unsigned Xcode projects do not yet do that. **Fix to complete in the Mac signing recipe:** receiver own default group first, KDE Connect group second, both using `$(AppIdentifierPrefix)`, same Personal Team, and inspect the issued profile. **Found:** comparing the signer with the project entitlement inputs. No second pairing is an alternative.


### Intel first run: missing Metal component

[Run 44848751393](https://github.com/Sparky-OS/flat-headset/actions/runs/44848751393), checked 2026-11-21, passed six of seven jobs at commit c11178e.
The Intel image reported `macos15 20260824.0482.1`, `x86_64`, Xcode 26.3 build 17C529 and iPhoneOS SDK 26.2.
KDE Connect and Cardboard built and packaged successfully on this host.
The static receiver libraries and link probe also built and uploaded before the app failed.
The arm64 image reported `macos26 20261117.0516.1`, Xcode 26.6 build 17F113 and SDK 26.5, and built all three apps.
All seven available artifact payloads passed their downloaded SHA-256 checks; there is no Intel receiver IPA for this run.
The five available IPAs contain unsigned arm64 programs for iOS 16.0 without embedded dynamic libraries/frameworks or provisioning profiles.
Both core archives contain eight static libraries and an unsigned arm64 link probe for iOS 16.0.

The selected Xcode Contents directory measured 4,515,932 KiB on the Intel host and 4,646,300 KiB on the arm64 host.
These are allocated-size measurements of those runner installations before the missing component is installed, not download sizes or total disk requirements including components stored elsewhere.

- **Symptom:** `CompileMetalFile` fails because the `metal` tool cannot execute without its Metal Toolchain.
- **Cause:** Xcode 26's optional Metal component was absent on the Intel runner. The log does not establish an Intel CPU or old-SDK source incompatibility.
- **Fix:** before compiling the core/app, execute `xcrun --sdk iphoneos metal --version`; if unavailable, visibly run `xcodebuild -downloadComponent MetalToolchain` on the hosted Mac, then verify the compiler again. Download failure or a still-unavailable compiler stops with a plain instruction. Nothing is fetched to the Linux workstation.
- **Found:** the complete failing app-build step names the missing component and prints the installation command. [Apple documents the separate Metal component](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components).

Xcode 26.3 remains selected for the next Intel attempt; only a green receiver build will establish it for all three programs.
The earlier LTO probe's x86_64 linker warnings were nonfatal capability-detection diagnostics; the configured core disables LTO and its actual arm64 libraries/probe passed.
Do not confuse those diagnostics with the app's Metal compilation failure.
The eventual real Mac setup also needs the Metal component, but installation/signing and SSH instructions wait for the complete Intel unsigned proof.
