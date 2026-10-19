# Build prerequisites

These are the source pins and commands behind the tested installation.
Run downloads, extraction, compilation and SDK tools inside an unprivileged container.
Mount one build-storage directory read-write at the same absolute path inside and outside the container, and an existing JDK 21 read-only.
Set HOME to a writable project directory.
Limit builds to four CPUs/jobs; the target build and test recipe used two jobs.
Do not mount display or audio sockets.
This document assumes a prepared Linux build image; creating or installing packages into a new image was not validated by this recipe.

Use `work` below for that absolute storage directory.
Use the active workspace disk floor, check `df -B1 "$work"` before large steps, and allow at least 8 GiB for the host build or 4 GiB per target module above that floor.
These are observed working allowances, not reservations against concurrent disk users.
The test wrapper accepts `QACI_RESERVE_GIB`; its historical default is 15 GiB, not an override of a newer workspace decision.
Save small configuration/install records and remove completed build trees.

## Pin the sources

| Repository | Revision |
|---|---|
| qt/qt5 (Coin definitions) | 1045923241fe388c5c7002e1e9e7c84d0d99b4ba |
| qt/qtbase | f9f500f0536fb0d8b4e3772cb5232d0fe3da741a |
| qt/qtshadertools | a6ece126662a4f3e654f35f5ff0456d8e587ba89 |
| qt/qtmultimedia (778399 PS9) | 1b10d5488200ee0c71f5db79512a6fca7dd84853 |
| KDAB/android_openssl | b71f1470962019bd89534a2919f5925f93bc5779 |

Fetch Qt sources from `https://code.qt.io/qt/<repository>.git`, the Gerrit patch set from `https://codereview.qt-project.org/qt/qtmultimedia` at `refs/changes/99/778399/9`, and KDAB's recipe from `https://github.com/KDAB/android_openssl.git`.
Place each under `src/`.
Check out the listed revisions and record any intentional changes.
Do not replace the Qt pins with qtmultimedia's older dependency-file revisions.
These are the local 6.13 dev pins, not a claim about the original Coin job's exact dependency commits.

## SDK and emulator

Use Google's command-line tools to install platform-tools, `platforms;android-37.0` and `build-tools;37.0.0` into `$work/sdk`, accepting the applicable SDK licenses.
The build uses JDK 21, Gradle 9.5.1 and AGP 9.2.1 as selected by this Qt revision.
A newer sdkmanager package is not a substitute for the pinned emulator or NDK when comparing CI behavior.

Download these public archives and check their hashes before extraction:

| Archive | Public base URL | SHA-1 |
|---|---|---|
| android-ndk-r27c-linux.zip | https://dl.google.com/android/repository/ | 090e8083a715fdb1a3e402d0763c388abb03fb4e |
| emulator-linux_x64-15917651.zip | https://dl.google.com/android/repository/ | 1b1f78891abf8ec268264356e1365c25519e8379 |
| x86_64-28_r11.zip | https://dl.google.com/android/repository/sys-img/google_apis/ | 1d93bd994e29c4e9bbe71fd9c278addc5418cbee |
| ffmpeg-9.0.2.tar.gz | https://ffmpeg.org/releases/ | 40c70cddcdc2e32b1b0fad2c85915c9145532452 |

Extract the NDK under `toolchains/`, the emulator under `sdk/`, and the image under `sdk/system-images/android-28/google_apis/`.
Link `sdk/ndk/27.2.12479018` to `toolchains/android-ndk-r27c`.
Keep actual command-line tools inside the local SDK: symlinking them to another SDK can make avdmanager inspect the wrong root.

Set `ANDROID_SDK_ROOT=$work/sdk`, `ANDROID_USER_HOME=$work/android-user` and `ANDROID_AVD_HOME=$work/avd`.
Create an AVD with `avdmanager create avd -n qt_api28_x86_64 -k 'system-images;android-28;google_apis;x86_64' -c 512M` and answer no to a custom hardware profile.
The archived emulator may lack sdkmanager's local `package.xml`.
If required, add generic local-package metadata for path `emulator`, revision `37.1.11`, matching its `source.properties`; never claim a different installed version.
After checking that revision is 37.1.11, write this to `sdk/emulator/package.xml`:

```xml
<?xml version="1.0"?>
<r:repository xmlns:r="http://schemas.android.com/repository/android/common/02"
 xmlns:g="http://schemas.android.com/repository/android/generic/02"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <localPackage path="emulator" obsolete="false">
  <type-details xsi:type="g:genericDetailsType"/>
  <revision><major>37</major><minor>1</minor><micro>11</micro></revision>
  <display-name>Android Emulator</display-name>
 </localPackage>
</r:repository>
```
 The test scripts verify acceleration and actual guest API/ABI at runtime.

## Host tools

Inside the prepared build container:

```bash
mkdir -p "$work/build/host-qtbase"
cd "$work/build/host-qtbase"
"$work/src/qtbase/configure" -prefix "$work/install/host" \
  -release -nomake tests -nomake examples -no-feature-sql \
  -no-feature-dbus -no-feature-printdialog -no-feature-cups
cmake --build . --parallel 4
cmake --install .
cmake -S "$work/src/qtshadertools" -B "$work/build/host-qtshadertools" -GNinja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$work/install/host" \
  -DCMAKE_INSTALL_PREFIX="$work/install/host" \
  -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF
cmake --build "$work/build/host-qtshadertools" --parallel 4
cmake --install "$work/build/host-qtshadertools"
```

Verify qmake reports 6.13.0, androidtestrunner starts, and qsb accepts a valid shader and rejects an invalid fixture.
Preserve install manifests and configuration, then remove both completed host build trees.

## OpenSSL and FFmpeg

Qt's pinned `coin/provisioning/common/unix/openssl_for_android.sh` documents the KDAB source-build recipe.
Use public OpenSSL 3.5.4; its SHA-256 is `967311f84955316969bdb1d8d4b983718ef42338639c621ec4c34fddef355e99`.
Apply KDAB's `ssl_3.patch`, configure `shared android-x86_64` with `-U__ANDROID_API__ -D__ANDROID_API__=23` and linker options `-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384`, then `make depend` and `make -j4 SHLIB_VERSION_NUMBER= build_libs`.
Set `ANDROID_NDK_ROOT`, `ANDROID_NDK_HOME` and the NDK LLVM bin PATH first.
Install headers at `install/openssl/include` and the `_3.so` libraries and static archives under `install/openssl/x86_64`; strip shared libraries with NDK llvm-strip.
Add `libssl.so`/`libcrypto.so` links to the `_3.so` files and an `x86_64/include` link to `../include`.
Check the exported version is `OPENSSL_3.0.0`, without an `OPENSSL_3_` variant suffix.

Use the pinned Qt `common/unix/install-ffmpeg-android.sh` together with its `ffmpeg-installation-utils.sh`, `common/shared/ffmpeg_config_options.txt` and `fix_ffmpeg_dependencies.sh`.
In a writable copy, remove its four `sudo ` prefixes and replace only `ffmpeg_source_dir=$(download_ffmpeg)` with your already checksum-verified, extracted source path.
Use public PatchELF **0.17.2** and invoke:

```bash
bash install-ffmpeg-android.sh --abi x86_64 \
  --ndk "$work/toolchains/android-ndk-r27c" \
  --openssl "$work/install/openssl" --page-size 16kb \
  --output "$work/install/ffmpeg-x86_64"
```

Check ELF64/x86_64 and 16 KiB load alignment.
Check FFmpeg config.h has GPL=0, NONFREE=0, OPENSSL=1 and MEDIACODEC=1.
Its avformat dependencies must name `libQt6FFmpegStub-ssl_x86_64.so` and `libQt6FFmpegStub-crypto_x86_64.so`.
Save config.h and remove intermediates.

## Target Qt

Set SDK/NDK variables and `GRADLE_USER_HOME=$work/gradle`.
Populate Gradle's cache using Qt's `cmake/QtSetupAndroid.cmake` with `ACTION_RESOLVE_GRADLE=ON`, `QT_ROOT_DIR=$work/src/qtbase`, `GRADLE_PROJECT_DIR=$work/src/qtbase/src/android/jar`, `GRADLE_BUILD_VARIANT=Release` and `QT_ANDROID_SDK_BUILD_TOOLS_REVISION=37.0.0` before offline configuration.

```bash
mkdir -p "$work/build/target-qtbase"
cd "$work/build/target-qtbase"
"$work/src/qtbase/configure" -prefix "$work/install/target" \
  -qt-host-path "$work/install/host" -release -force-debug-info \
  -nomake tests -nomake examples -qpa 'android;offscreen' \
  -android-ndk "$work/toolchains/android-ndk-r27c" -android-sdk "$work/sdk" \
  -android-abis x86_64 -- -DOPENSSL_ROOT_DIR="$work/install/openssl" \
  -DWARNINGS_ARE_ERRORS=ON -DQT_LINT_EXAMPLES=ON \
  -DCMAKE_C_COMPILER_FRONTEND_VARIANT=GNU -DCMAKE_CXX_COMPILER_FRONTEND_VARIANT=GNU
cmake --build . --parallel 2
cmake --install .
```

Check its installed manifest, save build records, leave the build directory and delete the intermediate tree.
Then build/install QtShaderTools followed by qtmultimedia, using the installed `lib/cmake/Qt6/qt.toolchain.cmake`, `CMAKE_BUILD_TYPE=RelWithDebInfo`, the same host/install prefixes, tests/examples OFF, warnings-as-errors ON, `QT_LINT_EXAMPLES=ON`, `FFMPEG_DIR=$work/install/ffmpeg-x86_64` and `QT_DEPLOY_FFMPEG=TRUE`.
For each module, the concrete configure/build/install commands are:

```bash
for module in qtshadertools qtmultimedia; do
  cmake -S "$work/src/$module" -B "$work/build/target-$module" -GNinja \
    -DCMAKE_TOOLCHAIN_FILE="$work/install/target/lib/cmake/Qt6/qt.toolchain.cmake" \
    -DCMAKE_INSTALL_PREFIX="$work/install/target" -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DQT_HOST_PATH="$work/install/host" -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF \
    -DWARNINGS_ARE_ERRORS=ON -DQT_LINT_EXAMPLES=ON \
    -DFFMPEG_DIR="$work/install/ffmpeg-x86_64" -DQT_DEPLOY_FFMPEG=TRUE
  cmake --build "$work/build/target-$module" --parallel 2
  cmake --install "$work/build/target-$module"
  # Save records and check installed files before removing this build tree.
  # Check free storage again before starting the next module.
done
```

Remove each module's intermediates after checking its install.
The three measured target trees were 2.2 GiB, 338 MiB and 802 MiB; the combined installation was 636 MiB.

Check the installed FFmpeg plugin and OpenSSL stub libraries exist and are ELF64/x86_64 with 16 KiB alignment.
Confirm qtmultimedia's cache enables FFmpeg and deployment and points to your installed target Qt.
The test recipe's runtime output then confirms the actual loaded backend/version.
Quick/QML modules were omitted from this focused configuration.

This recipe builds on the Qt Project and The Qt Company, Android/AOSP and Google, FFmpeg, KDAB, OpenSSL, Eelco Dolstra and PatchELF contributors, and the Linux/KVM, QEMU, compiler and build-tool projects.
Preserve their own licenses and contributor notices when distributing sources or binaries.
