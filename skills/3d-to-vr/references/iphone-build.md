# Building Flat Headset for iPhone from Linux

**For the contributor: write and test portable code on Linux, compile the native application on a standard hosted macOS runner, then sign and install from Linux.**
Check freshness first: source workflows and local gates checked 2026-11-20.
The first native proof target and workflow are implemented; a hosted build and phone launch are not yet established by the local checks.

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
   **How found:** the SDK-free compiler boundary followed by the hosted-build continuation; hosted execution still requires the first pushed run.
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
