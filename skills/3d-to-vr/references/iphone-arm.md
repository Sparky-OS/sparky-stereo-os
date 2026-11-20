# Native iPhone receiver from Linux

**For contributors porting the phone receiver: the measured Linux tool boundary, the SDK and signing prerequisites, and eight traps to check before an iPhone build.**
Check freshness first: source and SDK-free Linux probes checked 2026-11-20.
No native app build, provisioning, installation or optical qualification is established by these probes.

## Working recipe

1. Preserve the paired KDE Connect control plane, KRdp/FreeRDP picture and authenticated panel identity; the receiver's button is **Catch**.
2. Separate a tool that emits arm64 Mach-O from the Apple SDK it still needs: run the freestanding probe below without an SDK.
3. Read [Apple's Xcode and SDK agreement](https://www.apple.com/legal/sla/docs/xcode.pdf) before acquiring or using its files; the agreement restricts execution to an Apple-branded product running macOS.
   Reading a licence is not legal advice; the decision is Daniel's.
   Linux on Apple hardware does not itself meet the quoted macOS condition.
4. Keep personally acquired Apple files outside source repositories, evidence and bundles.
   The [SDK completion recipe](iphone-build.md) is an untested continuation, not a claim that an SDK alone produces the three applications.
5. Use a real terminal for the Linux [xtool](https://github.com/xtool-org/xtool) account step, `xtool auth login --mode password`.
   The person enters their own account, password and any verification code; a partner never supplies or records them.
   The observed prompt discloses virtual-Mac emulation and a third-party anisette service using a randomized token; reaching the prompt proves neither authentication nor signing.
6. Once the three reviewed IPAs exist, the person runs `python3 iphone-renew.py /path/to/private/iphone-apps.json` using [the renewal helper](../scripts/iphone-renew.py).
   The helper validates all three files and their hashes before invoking xtool, then targets one explicit USB UDID and stops on the first error.
   Its manifest contains exactly `kdeconnect`, `cardboard` and `flat-headset`, each with `path`, `sha256` and `bundle_id`, plus the top-level `udid`.
   It expects Python 3.11 or later, stable bundle IDs and builds without extensions or Watch apps.
   Authentication is a separate first setup or recovery step; the renewal command uses xtool's saved authentication.
7. On the phone, unlock, accept **Trust This Computer** for the intended computer, enable **Settings → Privacy & Security → Developer Mode**, restart and confirm if requested.
   If launch reports an untrusted developer, use **Settings → General → VPN & Device Management** to trust the developer shown for these apps; network access may be required for verification.
   Computer trust, developer trust, Developer Mode and KDE Connect pairing are four distinct steps.
8. Pair the receiver with the desktop, tap **Catch**, and count success only when the actual desktop arrives through RDP and both eyes are correct through the selected viewer.
   Validate expiry and renewal on the device before calling the seven-day operation proven.

## Build and installation boundary

Clang 21.1.8 and ld64.lld on Debian testing emitted an arm64 iOS object and a dylib without Apple's files:

```sh
printf 'int answer(void) { return 42; }\n' > tiny.c
clang --target=arm64-apple-ios16.0 -ffreestanding -fno-stack-protector -c tiny.c -o tiny.o
ld64.lld -arch arm64 -platform_version ios 16.0 16.0 -dylib -install_name @rpath/tiny.dylib tiny.o -o tiny.dylib
llvm-objdump --macho --private-headers tiny.dylib
```

The SDK version in that Mach-O header is an argument to the linker, not evidence of an installed SDK.
An include of `TargetConditionals.h` fails without the SDK; FreeRDP's iOS CMake platform initialization refuses the absent `iphoneos` SDK.
OpenSSL 3.6.0 and zlib configured but did not cross-compile without the platform C headers.
Do not fill the gap with Linux headers, fake Apple headers, or third-party repackaged SDKs.

Choose Clang/LLD for the native C/C++/Objective-C investigation and xtool for the provisioning/install investigation.
Theos is a build orchestrator and still needs an SDK and target libraries; its Linux installer offers SDK downloads, so do not run that installer as an SDK-free test.
The cctools-port configure probe stopped on missing libdispatch; that is a dependency result, not evidence that the project cannot work on Linux.
Its assembler/linker tools are not an SDK, a Swift compiler or an interface builder.
The upstream FreeRDP UI uses Xcode resources and is not a turnkey Linux app target.
A programmatic native UI avoids requiring Linux to run `ibtool`; the receiver still needs its own target and packaging.
Cardboard's existing Metal renderer compiles its shader source at runtime with `newLibraryWithSource`, so an offline Apple Metal compiler is not required by that renderer.

[Apple's free-account limits](https://developer.apple.com/help/account/basics/about-your-developer-account/) are three installed apps per device, ten registered App IDs and three registered devices, with seven-day expiry as specified on that page.
The three initial programs occupy all three application slots.
A phone-side signing helper would consume a slot too; the selected host-side xtool flow does not install such a helper.
Extensions have their own identifiers and profiles; omit unnecessary extension targets at build time rather than stripping signed packages later.
A fourth iStereo app cannot be promised alongside the first three under that limit.
Keep bundle IDs and the same signing identity stable across renewal to preserve application data; that preservation still requires a real install/refresh test.
Paid membership has a [100-device limit per product family per membership year](https://developer.apple.com/help/account/devices/devices-overview/), and profile lifetimes must be read from the issued profile; this work uses the free seven-day route.

## Panel pixels

Do not advertise a browser backing-store size as the physical panel.
[Apple lists the iPhone 8 Plus at 1920 × 1080 pixels and 401 ppi](https://support.apple.com/en-us/111950).
The iOS receiver must measure its window scene screen with `nativeBounds`/`nativeScale`, orient the dimensions for landscape and set the Metal drawable accordingly; UIKit `bounds` is in points.
The recorded 2208 × 1242 browser render size does not establish physical pixels or an RDP display mode.
Verify the native drawable and source-to-eye mapping on the device before accepting the descriptor.

## What crosses from Android

- Share the KDE Connect virtual-monitor packet schema and validation contract, not Kotlin or Android lifecycle code unchanged.
- Panel identity is the hash of the paired device certificate, not a model name or IP address; preserve panel geometry, refresh, physical measurements and profile ID.
- Preserve the five transport layouts (`native`, `sbs-720`, `tb-half-720`, `sbs-half-720`, `tb-720`) at the link boundary; they are not user-selectable output formats in the receiver.
- Share FreeRDP C sources and applicable edition patches after rebasing and validating them against the selected core; Android's pinned core differs from 3.28.0.
- Share Cardboard's C++ lens mesh and profile protobuf; use the existing Metal renderer and iOS profile storage adapter.
- Preserve the existing `shinecon-fit-d` fitted profile and its pixel-centred sampling semantics as a reference, without calling it a newly calibrated iPhone profile.
  The Android fitted shader uses strength 0.13; it is not a newly invented coefficient, and it is not interchangeable with a Cardboard QR radial coefficient.
  A physical image through the viewer is still required.
- Retain the ten languages and established words: English, Polish, Brazilian Portuguese, French, German, Spanish, Japanese, Korean, simplified and traditional Chinese.
- Port decode, Metal texture lifetime, display metrics, foreground/background handling, audio, QR capture and permission UI to iOS.

KDE Connect iOS has a TLS pairing backend but no `virtualmonitor` plugin in the audited revision.
Its ordinary background suspension means it cannot simply act as an Android-style permanent broker beside the foreground receiver.
Embed the KDE Connect protocol/backend in the receiver's foreground process and add the virtual-monitor protocol there; retain the separate KDE Connect program as requested.
Until shared keychain entitlements are actually provisioned and verified, each executable keeps its own paired identity and pairs explicitly with the same PC.
Do not export pairing secrets or RDP credentials through a custom URL.
Nonsensitive Cardboard viewer parameters can use a document import/export handoff.
[Shared keychain access](https://developer.apple.com/documentation/security/sharing-access-to-keychain-items-among-a-collection-of-apps) requires matching access groups and signing entitlements; common authorship alone does not grant it.

Flat Headset stays a static screen with no tracking.
iStereo later adds time-stamped head pose in a dynamic virtual channel belonging to the same authenticated RDP session, consumed by the PC's VR integration, plus the tracked presentation needed for games and spatial video.
Cardboard's iOS/CoreMotion sensor adapter and the tracked design carry over; a README mentioning ALVR or PhoneVR is not evidence of an implemented RDP pose channel.

## Traps

1. **Symptom:** `iphoneos is not an iOS SDK` or `TargetConditionals.h` is missing.
   **Cause:** a cross-target compiler does not contain Apple's sysroot.
   **Fix:** stop at the SDK prerequisite; after the licence decision, point the build at the person's separately acquired SDK.
   **Found by:** the Debian Clang/CMake probes, 2026-11-20.
2. **Symptom:** configure succeeds, then zlib includes host `bits/libc-header-start.h` or OpenSSL uses `/SDKs/`.
   **Cause:** missing target sysroot and missing OpenSSL `CROSS_TOP`/`CROSS_SDK`.
   **Fix:** isolate target headers/libraries, set those variables and check Mach-O architecture; configure success alone is not a build.
   **Found by:** the OpenSSL and zlib cross-build attempts.
3. **Symptom:** cctools-port says `Required library libdispatch not installed`.
   **Cause:** current port dependencies exceed the older binutils-only recipes.
   **Fix:** build its documented libdispatch/Blocks/TAPI dependencies if that linker is needed; Clang/LLD passed the freestanding route already.
   **Found by:** configure at ef969083; the dependency build remains untested.
4. **Symptom:** xtool password login aborts with NIO `epoll_ctl`/`Operation not permitted` before an account prompt.
   **Cause:** stdin was `/dev/null` in the isolated noninteractive container.
   **Fix:** run it in a real terminal and stop at the account prompt for an account-free probe.
   **Found by:** identical binary 1.24.0 failing without a TTY and reaching `Apple ID:` with one.
5. **Symptom:** Sideloader tries to download an Apple APK before asking for an account.
   **Cause:** that tool initializes its authentication dependency before prompting.
   **Fix:** keep account-free probes network-isolated and stop; do not treat a failed network request as a completed signing test.
   **Found by:** Dadoum Sideloader 1.0-pre4's bare invocation under `--network none`.
6. **Symptom:** all app roles plus a phone-side renewal helper do not fit the free account's app count.
   **Cause:** the helper itself occupies an app slot.
   **Fix:** use host-side renewal for the three initial apps; plan the later fourth app explicitly within Apple's limit.
   **Found by:** Apple's account-limit page and the helper's installation model, not a device experiment.
7. **Symptom:** the receiver loses its paired control broker after switching apps.
   **Cause:** iOS suspends ordinary background applications.
   **Fix:** keep the authenticated protocol endpoint in the foreground receiver; verify shared credentials separately if later used.
   **Found by:** the KDE Connect iOS lifecycle documentation and Apple lifecycle rules; receiver implementation pending.
8. **Symptom:** hardware decode is selected but a software decoder runs without an obvious product error.
   **Cause:** FreeRDP's FFmpeg VideoToolbox backend is marked experimental and contains fallback paths.
   **Fix:** surface the actual decoder and failure state; validate the negotiated pixel format and CVPixelBuffer-to-Metal path before making a hardware claim.
   **Found by:** FreeRDP 3.28.0 `libfreerdp/codec/CMakeLists.txt` and `h264_ffmpeg.c`; device verification pending.

## Primary source anchors

- [FreeRDP 3.28.0 iOS build instructions](https://github.com/FreeRDP/FreeRDP/blob/5370fb26fbf034ecd11d3026b6ad639b5fff493f/docs/README.ios): Xcode 26+, iOS 15+, CMake and dependencies; core Apache-2.0, legacy iOS files have MPL-2.0 notices.
- [Cardboard](https://github.com/googlevr/cardboard/tree/8bd424da7f1e399255a1b6e7c02be8e281ecc974/sdk): Apache-2.0, C++ lens math, iOS Metal renderer and sensor adapter.
- [KDE Connect iOS](https://invent.kde.org/network/kdeconnect-ios/-/tree/a303639652c1cf486bd6fb61335970723c2085a7): GPLv3 with its documented App Store enforcement exception; pairing backend, plugins and lifecycle.
- [xtool](https://github.com/xtool-org/xtool/tree/5318ebc7c0540f8e4c39d436c80604fa155d7a09): MIT, account authentication then integrated provisioning/signing/install.
- [Developer Mode](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device), [computer trust](https://support.apple.com/109054), [developer trust](https://help.apple.com/xcode/mac/current/en.lproj/dev96a12fb84.html).
