# RDP sensors and emulator preflight

Checked 2026-11-07 during integration preparation.
This recipe covers source and environment checks; it does not establish a working camera or pose channel.
Use the current source and preserve the later endpoint results separately.

## Working recipe

1. Record the embedded FreeRDP pin, patch series and the CMake module search order.
2. Inspect the embedding's camera flag, not only FreeRDP's upstream default.
3. Reserve space on the actual SDK/build filesystem before downloading and extracting each archive.
   Include toolchains selected by composite dependencies: the main app and Media3 can request different NDK revisions.
4. Verify the container image still exists, the Android/JDK tools load, and KVM is accessible inside the actual container.
5. Verify the emulator's API, ABI, virtual camera and sensor capabilities before building a claimed red/green endpoint comparison.
6. A missing APK, rejected launch or failed tool setup is an environment failure, not a passing negative transport test.

## Embedded camera configuration

Flat Headset's `android/freerdp-core/build.gradle.kts` selects both an upstream source pin and a CMake module directory.
Its `android/freerdp-core/cmake/ExternalFreeRDP.cmake` can override upstream's same-named file.
At the inspected baseline, upstream enables `CHANNEL_RDPECAM_CLIENT` while the embedding disables it.
Check both locations before concluding that camera support is absent upstream.

Record the native camera backend, codec configuration and selected API level together.
Android's NDK Camera2 API starts at API 24 and does not enumerate LEGACY-only camera devices.
An Android version alone therefore does not prove a usable NDK camera.
Read [Android's stable native APIs](https://developer.android.com/ndk/guides/stable_apis) and the current FreeRDP camera HAL.
Preserve the old receiver's supported API levels when adding camera linkage.

An advisory's publication date is not proof that a pinned commit lacks its fix.
Inspect the parser and the fixing commit.
For example, verify frame-rate denominator validation directly before describing a divide-by-zero as still present.
Review subsequent media-type validation, stream lifecycle and codec changes independently.
Do not replace a successful source inspection with a release-number assumption.

## SDK archives and disk accounting

Use the project-selected SDK, NDK and CMake revisions.
Resolve archive URLs, published checksums and sizes from the official repository metadata, then also retain a SHA-256 of the bytes used.
An archive's compressed size does not bound its extracted size.
Inspect its member sizes and top-level paths before extraction.

Do not strip one leading directory from every Android archive.
The inspected CMake archive has top-level `bin/`, `doc/` and metadata rather than one enclosing directory.
Flattening every archive identically caused a file/directory collision at `ninja`.
Use a package-specific layout and mark installation complete only after extraction and tool checks succeed.

Record both logical size and allocated size for emulator images.
Zero-filled image regions can consume substantial space after ordinary extraction.
If reclaiming those regions in an owned, stopped SDK image, preserve its logical size and compare complete file hashes before and after.
Never alter an image used by a running emulator, another worker or a physical device.
Use a separate writable AVD and keep the source system image immutable during tests.

## Recheck containers and JDK configuration

A recorded image tag can disappear after cleanup.
Inspect the selected image and architecture before launching it; use `--pull=never` when the intention is to reuse a local image.
This avoids an accidental registry lookup for a former local-only tag.
Keep a digest or image ID with the evidence, without assuming that it survives a reboot or cleanup.

Check KVM inside the container with the configured device and group access.
The tool shell's filesystem view may differ from the Docker daemon's device view.
A missing device in the shell is therefore not proof that the daemon cannot expose it.
Use headless software rendering and do not mount desktop display or audio sockets.

A bind-mounted distribution JDK may contain absolute links into its system configuration directory.
`java -version` can succeed while Gradle's HTTPS initialization fails.
It also does not prove that a Java compiler is installed.
Check `javac -version` and Gradle's detected toolchain capabilities; a JRE can occupy a directory whose name looks like a JDK.
Prefer a complete JDK provisioned inside the build container.
Observed symptoms included `Error loading java.security file` and `Couldn't parse jurisdiction policy files in: unlimited`.
Resolve the JDK's configuration links and provide its public security policy and trust configuration inside the container, or use a self-contained JDK distribution.
Do not copy credentials or private keys with that configuration.
Verify cryptographic initialization as well as the version before starting a long Gradle build.

The emulator launcher sets library search paths for its bundled libraries.
Running `ldd` on the QEMU executable without those paths can report bundled libraries as missing.
Distinguish those from missing system libraries such as `libpulse.so.0`, `libXi.so.6` or `libxkbfile.so.1`.
Install required system libraries only in the isolated build/test container, using the project's package and network policy.
Run `emulator -version` inside that container before allocating or booting an AVD.

Give the emulator and its ADB server a writable home directory inside the isolated test storage.
An otherwise working emulator failed to create its console token and ADB configuration when its container home resolved to `/`.
Apply the home setting to those container processes, without changing the host user's environment or reading console tokens or private keys.
Check the expected AVD registration and configuration files after `avdmanager`, then require an actual boot property from the selected emulator serial.
A successful command exit did not by itself establish that the requested AVD files existed.

The tested setup booted an API 28/x86_64 AOSP image with emulator 37.3.8, KVM and headless SwiftShader.
Camera-service enumeration reported two virtual cameras.
These results establish setup and enumeration only; no camera capture or RDP delivery follows from them.

## Composite build compatibility

Record the Android Gradle plugin version of the app and every substituted/composite build.
The prepared Flat Headset build selected AGP 9.2.1 while its Media3 source selected 9.1.1.
Gradle rejected that combination before app Java compilation with `Using multiple versions of the Android Gradle plugin ... in the same build is not allowed`.
Resolve the version mismatch explicitly and retain the changed source/toolchain pins; do not suppress the compatibility check or call that failure a negative RDP test.
Inspect dependency-selected SDK packages before allowing automatic downloads: the same build installed a second NDK while configuring Media3.
An extracted NDK can consume much more than its compressed download, independently of the app's own native build.

## Evidence boundary

Keep SDK/tool versions, source hashes, image identity, disk-reserve checks, command exit codes and failed setup logs.
A successful emulator version command proves that the executable loads; it does not prove boot, Camera2 capture, sensor fusion or RDP delivery.
For camera red/green proof, require a real channel-open result and changing received frames from the virtual camera.
For pose proof, require the selected fused source, captured timestamps and independently expected axes on both endpoints.
Retain permission-denied, unavailable-camera and absent-channel cases as distinct failures.
The host's real phone and its ADB server are outside an emulator-only test.

## Native compiler reports “no input files” after manual SDK extraction

Inspect the compiler entry with `ls -l` before changing compiler flags.
In a ZIP, a Unix symbolic link is marked by the file type in `external_attr`; its stored bytes are the link target, not a shell wrapper.
Extracting those bytes as a regular executable makes `clang++` try to execute `clang` without forwarding arguments, and makes the target compiler wrapper fail to locate `clang-20`.
Restore links from the same checksum-verified archive.
Preserve symlinks when extracting all SDK archives, validate that their targets remain inside the package, and retry a compiler probe before the application build.
In the recorded NDK r29 beta1 package, 37 links needed restoration; Cardboard then compiled and freeRDPCore reached its native build.
This is a toolchain result, not a camera-channel test.

## Removing a camera OFF argument still leaves the channel absent

Read both the generic channel options and the Android external-build wrapper.
FreeRDP's `channels/rdpecam/ChannelOptions.cmake` defaults the client to OFF, while its Android `ExternalFreeRDP.cmake` explicitly selects ON.
An embedding that replaces that wrapper must retain the Android ON setting.
Check the actual native CMake cache; absence of an OFF argument does not prove enablement.
Keep a camera-disabled APK as the endpoint control.

## A supported channel appears absent before the first connection

The Android Java class queries camera support while it initializes, before a session registers its addin provider.
`freerdp_load_channel_addin_entry` depends on that provider.
The compiled-table query `freerdp_channels_load_static_addin_entry` can inspect built-in support at this point.
A native check with the known built-in display-control channel returned indirect=0, static=1 before a session; an invented channel returned 0.
This checks lookup semantics, not Android camera delivery.
Also keep channel presence separate from optional pixel conversion: raw NV12 passthrough does not require an NV12-to-I420 converter.

## KRdp cannot find encoderPaused or setEncoderPaused

An otherwise matching Qt/KF SDK can still contain an older KPipeWire API.
Inspect the KRdp commit that introduced backpressure and the KPipeWire public header.
Upstream KPipeWire's `PipeWireBaseEncodedStream` supplies these methods; they are absent from the packaged 6.7.4 API used in the failed build.
Build the matching upstream dependency into an isolated prefix and pass that prefix and its `KPipeWire_DIR` to CMake.
Do not remove the caller's backpressure to make an older SDK compile.
The recorded dependency source is KDE/kpipewire `bb838b0371012b99b5c199b7aaf662be319ae5b6`; KRdp subsequently built against that prefix and its two registered tests passed.
This establishes a build/test baseline, not display or pose delivery.

## TLS fixture stalls before a channel can negotiate

Read the client log as well as the server log.
In the recorded failed attempt, the Android client invoked `OnAuthenticate` after selecting TLS, then waited in the stock credential dialog.
The server's later `BIO_do_handshake failed` was not a camera-channel rejection.
A TLS-only, unauthenticated test server can still need explicit public dummy credentials in this client.
An independent instrumentation APK subsequently supplied the public dummy password and the pinned test-certificate fingerprint to the unchanged control APK.
The control then connected successfully.
Keep the same driver for both builds so a credential-dialog fix does not require rebuilding the preserved negative control.
Require RDP connection and DVC readiness before calling a camera-disabled timeout the endpoint red control.

## Relocating the SDK, build cache and stopped emulator

Move bulky SDK, Gradle, source/build and AVD directories to the authorized build filesystem rather than reducing a reserve.
Check the destination reserve before each copy, including logical image size as a conservative bound.
Preserve Unix symlinks and sparse image extents (`cp --archive --sparse=always`), compare file/link metadata and hashes of ordinary files, then remove the old copy.
Do not inspect private key or token contents as part of that verification.
A recorded migration verified five directory trees; this establishes their relocation, not that their tools start afterward.

Set `ANDROID_HOME`/`ANDROID_SDK_ROOT`, `GRADLE_USER_HOME` and `ANDROID_AVD_HOME` to the new locations.
Update the AVD registration's `path` and its `image.sysdir.1` setting.
Repair a moved Git worktree with `git worktree repair "$new_worktree"` from its owning repository.
Invalidate generated `.cxx` directories that cache absolute source/compiler paths; retain authored sources and dependency pins.
Check QCOW2 backing filenames as metadata before booting a moved AVD; relative userdata/cache backings remained valid in the recorded move.
Do not change guest key images while investigating storage paths.

Check the configured Docker socket before interpreting a launch failure as an SDK regression.
A socket node can remain on disk while connection attempts return `ECONNREFUSED`.
The recorded relocation could be checked statically, but neither the emulator nor Gradle could be restarted through that unavailable lane proxy.
Restore the authorized proxy and repeat actual startup checks before claiming the relocated environment works.


## RDP connects but the server never reaches DVC readiness

Do not let `WTSVirtualChannelManagerCheckFileDescriptor` auto-open the manager during the pre-activation handshake.
The inspected FreeRDP implementation records `DRDYNVC_STATE_INITIALIZED` on its first open attempt, even if the static channel is not yet usable.
Follow KRdp's lifecycle: require an activated peer and joined `drdynvc`, open once, and use `WTSVirtualChannelManagerCheckFileDescriptorEx(manager, FALSE)` in the event loop.
With this correction the preserved camera-disabled client reached `RDP_CONNECTED`, `RDP_ACTIVE` and `DVC_READY`.
That proves the fixture's transport setup, not camera enumeration or sample delivery.

## APK builds but dlopen reports liburiparser.so missing

A successful native link and camera-only symbol check do not establish the APK's runtime dependency closure.
Inspect `DT_NEEDED` in every packaged library and compare each dependency with the same ABI's APK entries and the selected NDK platform stub directory.
The camera-enabled candidate passed the focused eager-Camera2 check but failed to start because `libwinpr3.so` needed an omitted `liburiparser.so`.
A closure check detected the omission independently of the emulator crash.

When adding an imported CMake library, inspect AGP's `android_gradle_build.json` runtime-files list as well as CMake's current file-api reply.
In the recorded incremental build, the new URI-library link appeared in CMake's reply and the JNI ELF, but the older AGP runtime-files list still omitted it; the rebuilt APK remained broken.
Regenerate and verify the packaging model before treating an imported-target addition as a fix.
The verified fix is a module-local `CMakeLists.txt` used as Gradle's native entry point, with the prepared upstream CMake project added as a subdirectory.
AGP then records the embedding's `.cmake` overrides in `buildFiles` and `build_file_index.txt`.
Its file-api parser retains `.cmake` inputs inside the native source root; the previous generated upstream entry point left the overrides outside that root.
The inspected build had Gradle's configuration cache disabled, so clearing that cache was unrelated.
The filter is visible in [AGP's CmakeFileApiV1.kt](https://android.googlesource.com/platform/tools/base/+/refs/heads/mirror-goog-studio-main/build-system/gradle-core/src/main/java/com/android/build/gradle/internal/cxx/cmake/CmakeFileApiV1.kt).
The local AGP 9.2.1 bytecode confirmed the same rule.

Declare an external shared library in `ExternalProject_Add(BUILD_BYPRODUCTS ...)` as well as in its imported target.
A clean Ninja graph otherwise reports that the library is missing with no known rule to make it; an existing dependency prefix can hide this error.
The URI library now participates in the normal native build and packaging graph.

Prove incremental tracking by removing the imported target from the scratch build's override and rebuilding without a clean: the model must drop the runtime library and the closure check must fail.
Restore the target and rebuild: the model must include it and closure must pass.
The recorded test passed in both directions while `prepareFreeRdp` stayed up to date; no `.so` was copied by hand and no cache was manually deleted.
The resulting APK also loaded its native core and connected in the API-28 emulator.
Camera enumeration and frame delivery are separate gates.


## RDPECAM negotiates but Android announces no camera without an H.264 encoder

Check the HAL log after the version exchange, not only the channel-open result.
The recorded client loaded the Android HAL and negotiated version 2, then logged `no conversion of NV12 frames to H.264` and announced no device.
The existing video converter supports same-format raw NV12 passthrough without that encoder.
The enumeration-only H.264 gate therefore hid a usable path before the normal supported-format selection ran.
A local patch removes that gate and leaves format selection to `GetMediaTypeDescriptions`.
With that patch and a matching source-built server, the API-28 emulator delivered twelve raw NV12 frames at 640×480, each 460,800 bytes, with ten distinct frame hashes.
After disconnect both virtual cameras reported closed with no client instance.
This establishes raw-frame transport and session teardown in the emulator, not compressed-camera encoding or physical-device behavior.
Current upstream source, recent file commits, related issues and merged encoder changes were checked before writing the patch.

For the camera-disabled control, require a connected, activated RDP peer, DVC readiness and an explicit negative camera-enumerator creation status, with zero frames and no version exchange.
A fixture now reports `ABSENT_CHANNEL_CONTROL PASS` only when all those conditions hold.
Keep the enabled build's version negotiation with zero frames as a distinct backend failure.
Set `CAM_SELECT_VERSION_RESPONSE.Header.MessageId` to `CAM_MSG_ID_SelectVersionResponse`; zero-initializing that caller-owned structure does not set its message type.


## Server rejects CAM_MEDIA_TYPE_DESCRIPTION_FLAGS 0

Check both endpoints' FreeRDP revisions.
The packaged 3.32.1 server rejected flags zero before its media-type callback ran, although the newer client correctly advertised raw NV12 without decoding or bottom-up flags.
[MS-RDPECAM 2.2.3.8.1](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpecam/) permits zero or more defined flags.
Upstream [faeeb6ae6f84](https://github.com/FreeRDP/FreeRDP/commit/faeeb6ae6f84d9815af96e8b1967f3f295c648d6) corrects the shared validator.
Build the matching server libraries into an isolated prefix and compile the fixture against that prefix.
Verify `pkg-config --modversion` and `ldd` so the loader actually uses the new FreeRDP and WinPR libraries.
The matched 3.33.1 server accepted the raw mode and received changing samples; the same fixture binary passed the original camera-disabled negative control.
Do not bypass the server parser or change valid client flags to satisfy an older validator.

## Pose appears fresh after transport delay, or held input survives loss

Test capture time separately from receive time.
A receipt-time mutant that replaces the mapped sensor time with `now` must fail the unchanged stale-input test.
The recorded core uses eight startup clock exchanges, the lowest residual delay and an explicit drift margin; a nominal clock sync does not qualify a physical latency claim.
The prototype refreshes every 250 ms after startup so the eight-sample window does not retain an estimate past the declared uncertainty budget.
Reject a discontinuity or excessive uncertainty rather than substituting receipt time.

Bind source registration to one authenticated RDP peer, active input approval, session, lease, seat and owned output before delivering any pose.
Release held actions on stale input and on revoked permission, then unregister on disconnect.
Exercise wrong peer, absent lease, missing approval, revocation, replay and changed epochs with a consumer that can observe invalidation.
Drop an old captured sample before interpreting its source-epoch metadata; otherwise a delayed old source can spuriously request recentering.
The recorded core has a regression for this ordering.

Test mounting with independent literal device-axis rotations and expected forward/up rays for both landscape directions.
A wrong-mount and w-first quaternion control must fail.
Keep source confidence unknown when Android supplies only an accuracy enum; do not invent measured translation from a neck model.
The common stereo-pointer contract remains proposed until its permission and output adapter exists.
A synthetic-grant test client demonstrates the consumer seam without granting compositor input authority.

## Pose freezes only after another packet arrives

An RDP worker blocked indefinitely on socket events cannot enforce a 100 ms freshness deadline for an idle peer.
When tracking is explicitly configured, use a bounded wait and poll freshness even if no event arrives.
The prototype polls at 10 ms, freezes at 100 ms and exposes lost tracking at 250 ms.
An ordinary untracked RDP connection retains its existing wait behavior.
Read the peer's WTS session id with `WTSQuerySessionInformationA(manager, WTS_CURRENT_SESSION, WTSSessionId, ...)` before opening a DVC.
The OS console session id is not the peer's FreeRDP virtual-channel manager id.

The integrated KRdp build passed its existing module smoke and panel tests plus five pose core suites.
The pre-pose APK connected to the actual receiver, activated RDP, explicitly rejected the pose DVC and delivered zero poses.
The Android fused-sensor endpoint still requires its own positive qualification; core tests and a negative endpoint control do not establish it.

## Core tests pass but the Android pose path is still unqualified

Run the receiver's standalone core tests inside its SDK container:

```sh
cmake -S autotests/stereotracking -B build/pose-core -G Ninja
cmake --build build/pose-core -j4
ctest --test-dir build/pose-core --output-on-failure
```

Then run an actual phone-side fused sensor through the DVC to the integrated KRdp receiver.
The recorded API-28 AOSP emulator advertises game and compass rotation vectors, with a 100 Hz minimum-period limit.
It delivered 338 framework-fused game samples at 56.07 Hz for a 60 Hz selection, with increasing source and mapped timestamps and 0.55–2.56 ms estimated clock uncertainty.
Separate 30 Hz, 90 Hz and compass selections delivered real virtual-sensor samples; a requested 120 Hz was explicitly unavailable, without substitution.
Those measurements establish emulator delivery, not physical sensor accuracy or end-to-end display latency.

Keep deterministic Android adapter proof separate from virtual sensor-fusion proof.
Inject literal rotation vectors through the same `SensorManager.getQuaternionFromVector` conversion used by live callbacks, reorder its wxyz result to wire xyzw, and join the PC's original source timestamp to the injected fixture.
The recorded two landscape runs compare all six signed physical-axis rotations, identity and sign continuity against independent forward/up expectations.
Pause/resume increments the sensor source epoch and requires recentering before delivery resumes.
A simulated 500 ms writer stall delivered no old in-flight pose; recovery required fresh input and retained the origin.
This models blocked transport; it does not qualify concurrent camera saturation on physical hardware.

## A blocked pose writer accumulates old sensor samples

Use one latest-sample mailbox and one network writer, rather than posting a runnable for every sensor callback.
A blocked-writer test offered 10,000 readings and required the next unsent reading to be the newest, followed by an empty mailbox.
Replacing the mailbox with an unlimited FIFO made that unchanged test fail.
Keep the compiled mutant outside authored sources and verify their bytes remain unchanged.
The phone's controller uses that tested mailbox; its control queue is separately bounded and rejects overflow.

## Phone shows disconnected instead of the actual pose error

Inspect both endpoints before accepting a named error gate.
The receiver originally queued an error STATUS and immediately called `WTSVirtualChannelClose`; that discarded the unsent status, so Android saw only peer disconnect.
Invalidate and unregister input immediately, then allow a bounded manager-drain period before closing the optional DVC.
The recorded 100 ms drain delivered the explicit unavailable-rate and revoked-permission errors to Android, while sources were already invalidated and unregistered.
Start test revocation and measurement timers at peer activation, not at process creation; slow app startup otherwise revokes the synthetic grant before the test even connects.
A connection/activation timeout remains separately bounded.

## New Android source uses a Java method newer than minSdk

Inspect the packaged dex as well as the source API level.
`Long.compareUnsigned` is API 26 in the SDK metadata, but the recorded minSdk-23 build enables core-library desugaring and its packaged pose-adapter dex contains no reference to that platform method.
This bounded inspection avoids inventing an API compatibility failure from source spelling alone.
It does not replace running the supported older Android images.

## A correct transport proof hides overlapping headset status

Capture the production headset activity, not only a debug session activity, before accepting new visible controls.
The first two-eye capture showed the new pose status overlapping the existing link readout.
Moving pose status to the bottom separates the readouts; leave the centre alignment margin uncovered.
Repeat the labels identically in both eyes and inspect the resulting full side-by-side capture.
A receiver that sends no desktop picture still leaves the original waiting scene visible behind the status; do not describe that capture as streamed-video proof.
