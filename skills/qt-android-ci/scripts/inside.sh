#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
mode=${1:?Use build or run}
exec > "$QACI_LOGS/$mode.log" 2>&1
export ANDROID_SDK_ROOT="$QACI_WORK/sdk"
export ANDROID_NDK_ROOT="$QACI_WORK/toolchains/android-ndk-r27c"
export ANDROID_USER_HOME="$QACI_WORK/android-user"
export ANDROID_AVD_HOME="$QACI_WORK/avd"
export GRADLE_USER_HOME="$QACI_WORK/gradle"
export PATH="$JAVA_HOME/bin:$PATH"

check_disk() {
    df -B1 "$QACI_WORK"
    local available
    available=$(df --output=avail -B1 "$QACI_WORK" | tail -1)
    (( available >= (15 + $1) * 1024 * 1024 * 1024 )) || {
        echo "Need 15 GiB reserve plus $1 GiB for this step" >&2
        return 1
    }
}

android_build="$QACI_BUILD/android-build-tst_qvideoframebackend"
if [[ "$mode" == build ]]; then
    export QT_QPA_PLATFORM=offscreen
    check_disk 3
    mkdir -p "$ANDROID_SDK_ROOT/ndk"
    if [[ ! -e "$ANDROID_SDK_ROOT/ndk/27.2.12479018" ]]; then
        ln -s "$ANDROID_NDK_ROOT" "$ANDROID_SDK_ROOT/ndk/27.2.12479018"
    fi
    cmake -S "$QACI_SOURCE" -B "$QACI_BUILD" -GNinja \
        -DCMAKE_TOOLCHAIN_FILE="$QACI_WORK/install/target/lib/cmake/Qt6/qt.toolchain.cmake" \
        -DQT_HOST_PATH="$QACI_WORK/install/host" -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DANDROID_SDK_ROOT="$ANDROID_SDK_ROOT" -DANDROID_NDK_ROOT="$ANDROID_NDK_ROOT" \
        -DWARNINGS_ARE_ERRORS=ON -DQT_BUILD_TESTS=ON -DQT_USE_TARGET_ANDROID_BUILD_DIR=ON \
        -DFFMPEG_DIR="$QACI_WORK/install/ffmpeg-x86_64" -DQT_DEPLOY_FFMPEG=TRUE
    setsid cmake --build "$QACI_BUILD" --parallel 2 --target tst_qvideoframebackend_make_apk &
    build_pid=$!
    while kill -0 "$build_pid" 2>/dev/null; do
        if ! check_disk 2; then
            kill -TERM -- "-$build_pid" || true
            wait "$build_pid" || true
            exit 1
        fi
        sleep 10
    done
    wait "$build_pid"
    exit
fi
[[ "$mode" == run ]]
check_disk 2
cd "$android_build"
timeout 180 ./gradlew --offline help > "$QACI_LOGS/gradle-warmup.log" 2>&1
export QT_QPA_PLATFORM=android QT_MEDIA_BACKEND=ffmpeg QTEST_ENVIRONMENT=ci
adb="$ANDROID_SDK_ROOT/platform-tools/adb"
emulator="$ANDROID_SDK_ROOT/emulator/emulator"
"$emulator" -accel-check
"$emulator" -avd "$QACI_AVD" -accel on -no-window -no-audio \
    -gpu swiftshader -no-boot-anim -cores 2 -memory 4096 \
    -partition-size 2048 -no-snapshot -no-nested-warnings \
    > "$QACI_LOGS/emulator.log" 2>&1 &
emulator_pid=$!
trap 'kill "$emulator_pid" 2>/dev/null || true; wait "$emulator_pid" || true' EXIT
timeout 180 "$adb" wait-for-device
ready=0
for ((attempt=0; attempt<180; attempt++)); do
    kill -0 "$emulator_pid"
    boot=$(timeout 2 "$adb" shell getprop sys.boot_completed | tr -d '\r\n')
    complete=$(timeout 2 "$adb" shell getprop dev.bootcomplete | tr -d '\r\n')
    if [[ "$boot" == 1 && "$complete" == 1 ]]; then
        ready=1
        break
    fi
    sleep 1
done
test "$ready" = 1
api=$("$adb" shell getprop ro.build.version.sdk | tr -d '\r\n')
abi=$("$adb" shell getprop ro.product.cpu.abi | tr -d '\r\n')
printf 'boot_completed=%s dev.bootcomplete=%s API=%s ABI=%s\n' "$boot" "$complete" "$api" "$abi"
[[ "$api" == 28 && "$abi" == x86_64 ]]
printf -v make_command 'cmake --build "%s" --target tst_qvideoframebackend_make_apk --parallel 2' "$QACI_BUILD"
set +e
timeout 360 "$QACI_WORK/install/host/bin/androidtestrunner" \
    --path "$android_build" --adb "$adb" --ndk-stack "$ANDROID_NDK_ROOT/ndk-stack" \
    --apk "$android_build/tst_qvideoframebackend.apk" --make "$make_command" \
    --timeout 240 --show-logcat --verbose -- -o "$QACI_LOGS/qtest.txt,txt" \
    > "$QACI_LOGS/runner.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$QACI_LOGS/exit.txt"
"$adb" logcat -d -b crash > "$QACI_LOGS/crash.log"
"$adb" emu kill
wait "$emulator_pid"
trap - EXIT
exit "$result"
