# Completing the iPhone build after the SDK prerequisite

**For the build contributor: an untested SDK-dependent continuation of the SDK-free compiler probes.**
Checked against FreeRDP 3.28.0 sources and Apple's compatibility table on 2026-11-20.
These commands have not run with Apple's files and are not a finished three-app build system.
They contain no SDK download, account login or device operation.

## Select and locate the SDK

The native investigation selects **Xcode 26.0.1, iPhoneOS 26.0 SDK, arm64, minimum deployment target 16.0**.
The SDK version need not equal the installed iOS version.
[Apple's compatibility table](https://developer.apple.com/xcode/system-requirements/) lists iOS 15–26 deployment targets and iOS 15+ device support for Xcode 26.0.1, with Swift 6.2; this includes iOS 16.
FreeRDP 3.28.0's revived iOS client asks for Xcode 26 or later, so an old Xcode 14/iOS 16 SDK is not the selected baseline.
The selection is a compatible candidate, not a measured minimum SDK for every reused source file.

After the person's licence decision, they obtain Xcode 26.0.1 themselves from [Apple's downloads](https://developer.apple.com/download/all/?q=Xcode%2026.0.1).
The Universal archive is the relevant host variant for Intel Macs, although this recipe uses the SDK as target files and does not run the bundled macOS executables on Linux.
Archive byte size and extracted SDK byte size were **not verified** from Apple's unauthenticated pages; record the authenticated listing's size and `stat`/`du` results before selecting extraction space.
Do not substitute a remembered size for a measurement.
The SDK is under:

```text
Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk
Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include/c++/v1
```

The first path may be a symlink to a versioned `iPhoneOS26.0.sdk`.
Resolve it inside the external SDK store; keep the C++ headers, target Swift resources and framework module maps with their provenance when needed.
Extracting a modern `.xip` on Linux needs an extractor that handles its pbzx payload; xtool's SDK builder contains that extraction logic, but it also builds and transforms a Swift SDK.
Do not equate successful `xtool --help` with a tested SDK extraction.
Current xtool documentation asks for Swift 6.4 and Xcode 27.1; pairing that flow with Xcode 26.0.1/Swift 6.2 remains untested.
Use xtool's measured signing CLI independently; validate the Swift build toolchain separately before promising the complete KDE Connect iOS build.

## Native dependency continuation, not yet run

Run in an isolated Linux build container, at most four build threads, with source inputs read-only and the external SDK mounted read-only.
All source downloads happen separately; these commands do not fetch dependencies automatically.
FreeRDP 3.28.0 pins OpenSSL 4.0.1 and FFmpeg n8.1 in `cmake/DepVersions.cmake`; use those revisions and its source hashes for the completion build.
The first SDK-free dependency probe used OpenSSL 3.6.0; a follow-up used the upstream-pinned OpenSSL 4.0.1 and FFmpeg n8.1.
Use the recorded zlib revision, and do not call a build against different dependency revisions the same tested configuration.
Set these absolute paths to existing inputs and a separate writable build directory:

```sh
export IOS_SDK=/path/to/external/SDKs/iPhoneOS26.0.sdk
export IOS_CXX_HEADERS=/path/to/external/XcodeDefault.xctoolchain/usr/include/c++/v1
export OPENSSL_SRC=/path/to/openssl
export ZLIB_SRC=/path/to/zlib
export FFMPEG_SRC=/path/to/ffmpeg
export FREERDP_SRC=/path/to/freerdp
export IOS_WORK=/path/to/ios-build
```

First establish the sysroot, compiler and linker rather than using host include directories:

```sh
set -eu
test -f "$IOS_SDK/usr/include/TargetConditionals.h"
test -f "$IOS_CXX_HEADERS/vector"
mkdir -p "$IOS_WORK/bin" "$IOS_WORK/deps" "$IOS_WORK/openssl" "$IOS_WORK/zlib" "$IOS_WORK/ffmpeg"
export IOS_DEPS="$IOS_WORK/deps"
cat > "$IOS_WORK/bin/ios-clang" <<'SH'
#!/bin/sh
exec clang --target=arm64-apple-ios16.0 -isysroot "$IOS_SDK" -fuse-ld=lld "$@"
SH
cat > "$IOS_WORK/bin/ios-clang++" <<'SH'
#!/bin/sh
exec clang++ --target=arm64-apple-ios16.0 -isysroot "$IOS_SDK" -nostdinc++ -isystem "$IOS_CXX_HEADERS" -fuse-ld=lld "$@"
SH
chmod +x "$IOS_WORK/bin/ios-clang" "$IOS_WORK/bin/ios-clang++"
export CC="$IOS_WORK/bin/ios-clang"
export CXX="$IOS_WORK/bin/ios-clang++"
export AR=llvm-ar RANLIB=llvm-ranlib NM=llvm-nm
export CROSS_TOP="$(dirname "$(dirname "$IOS_SDK")")"
export CROSS_SDK="$(basename "$IOS_SDK")"
cd "$IOS_WORK/openssl"
"$OPENSSL_SRC/Configure" ios64-cross no-shared no-tests no-asm --prefix="$IOS_DEPS"
make -j4 build_libs
make -j4 install_dev
cd "$IOS_WORK/zlib"
"$ZLIB_SRC/configure" --static --prefix="$IOS_DEPS"
make -j4 libz.a
make -j4 install
```

FFmpeg supplies the upstream FreeRDP VideoToolbox path; a direct zero-copy adapter is additional receiver work, not provided by these switches:

```sh
cd "$IOS_WORK/ffmpeg"
"$FFMPEG_SRC/configure" --prefix="$IOS_DEPS" --enable-cross-compile --target-os=darwin --arch=arm64 \
  --cc="$CC" --cxx="$CXX" --ar=llvm-ar --ranlib=llvm-ranlib --nm=llvm-nm --sysroot="$IOS_SDK" \
  --enable-static --disable-shared --enable-pic --disable-gpl --disable-autodetect \
  --disable-programs --disable-doc --disable-debug --disable-network --disable-everything \
  --disable-avdevice --disable-avformat --disable-avfilter --enable-swscale --enable-swresample \
  --enable-avcodec --enable-avutil --enable-decoder=h264 --enable-parser=h264 \
  --enable-decoder=hevc --enable-parser=hevc --enable-videotoolbox \
  --enable-hwaccel=h264_videotoolbox --enable-hwaccel=hevc_videotoolbox
make -j4
make -j4 install
```

Configure the portable core without the upstream Xcode UI target:

```sh
cat > "$IOS_WORK/ios.cmake" <<'CMAKE'
set(CMAKE_SYSTEM_NAME iOS)
set(CMAKE_SYSTEM_PROCESSOR arm64)
set(CMAKE_OSX_ARCHITECTURES arm64)
set(CMAKE_OSX_DEPLOYMENT_TARGET 16.0 CACHE STRING "")
set(CMAKE_OSX_SYSROOT "$ENV{IOS_SDK}" CACHE PATH "")
set(CMAKE_C_COMPILER "$ENV{IOS_WORK}/bin/ios-clang")
set(CMAKE_CXX_COMPILER "$ENV{IOS_WORK}/bin/ios-clang++")
set(CMAKE_AR llvm-ar)
set(CMAKE_RANLIB llvm-ranlib)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(CMAKE_FIND_ROOT_PATH "$ENV{IOS_SDK}" "$ENV{IOS_DEPS}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
CMAKE
export PKG_CONFIG_LIBDIR="$IOS_DEPS/lib/pkgconfig"
export PKG_CONFIG_PATH=
cmake -S "$FREERDP_SRC" -B "$IOS_WORK/freerdp" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$IOS_WORK/ios.cmake" -DIOS=ON \
  -DCMAKE_INSTALL_PREFIX="$IOS_DEPS" -DCMAKE_PREFIX_PATH="$IOS_DEPS" \
  -DOPENSSL_ROOT_DIR="$IOS_DEPS" -DOPENSSL_USE_STATIC_LIBS=ON \
  -DBUILD_SHARED_LIBS=OFF -DWITH_CLIENT=OFF -DWITH_CLIENT_COMMON=ON \
  -DWITH_CLIENT_SDL=OFF -DWITH_SERVER=OFF -DWITH_SAMPLE=OFF \
  -DWITH_MANPAGES=OFF -DWITH_SYSTEMD=OFF -DWITH_X11=OFF -DWITH_WAYLAND=OFF \
  -DWITH_CUPS=OFF -DWITH_PCSC=OFF -DWITH_KRB5=OFF -DWITH_OPENSSL=ON \
  -DWITH_INTERNAL_RC4=ON -DWITH_INTERNAL_MD4=ON -DWITH_INTERNAL_MD5=ON \
  -DWITH_FFMPEG=ON -DWITH_VIDEO_FFMPEG=ON -DWITH_DSP_FFMPEG=ON \
  -DWITH_SWSCALE=ON -DWITH_VIDEOTOOLBOX=ON -DWITH_OPENH264=OFF
cmake --build "$IOS_WORK/freerdp" --parallel 4
cmake --install "$IOS_WORK/freerdp"
```

Inspect generated compile commands for host header/library leakage, unused CMake options and missing optional dependency errors.
Do not disable TLS or certificate verification to obtain a successful build.
Use `llvm-ar t` and `llvm-objdump --macho --private-headers` on extracted archive members to establish arm64 target identity.
Link a small UIKit application before treating static archives as usable; this will expose missing Apple frameworks, `.tbd` support or target compiler-rt builtins.
The latter must be an iOS runtime built or supplied for that target, never Linux's runtime archive.
No claim is made yet that the full app links.

## Application targets still to implement

Create three native targets with stable bundle IDs, minimum iOS 16.0 and no unnecessary app extensions: the KDE Connect port, the Cardboard profile program and Flat Headset.
Retain licences: FreeRDP Apache-2.0 core, MPL-2.0 for any reused iOS client files, Cardboard Apache-2.0 and KDE Connect GPLv3 with its existing exception text.
Build native screens programmatically; put launch metadata and icons into each app bundle without silently assuming `xcodebuild`, `ibtool` or `actool` exists on Linux.
The complete KDE Connect UI is Swift/Objective-C and still needs a validated compatible Swift cross-toolchain; replacing it with a stub is not a completed port.
Use the original profile protobuf and C++ mesh logic, Cardboard's Metal renderer, and iOS-specific platform adapters; QR scanning must use a native camera implementation.
Package each app as `Payload/Name.app` in its IPA, then produce the three-file SHA-256 manifest consumed by the renewal helper.
Provisioning must establish the permitted entitlements for that account; unsigned or ad-hoc Mach-O output does not authorize installation on a stock phone.
