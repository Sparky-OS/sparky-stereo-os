# RDP sensors and emulator preflight

Checked 2026-11-06 during integration preparation.
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

Inspect the compiler entry with `ls -l` before changing compiler flags. In a ZIP,
a Unix symbolic link is marked by the file type in `external_attr`; its stored
bytes are the link target, not a shell wrapper. Extracting those bytes as a
regular executable makes `clang++` try to execute `clang` without forwarding
arguments, and makes the target compiler wrapper fail to locate `clang-20`.
Restore links from the same checksum-verified archive. Preserve symlinks when
extracting all SDK archives, validate that their targets remain inside the
package, and retry a compiler probe before the application build. In the
recorded NDK r29 beta1 package, 37 links needed restoration; Cardboard then
compiled and freeRDPCore reached its native build. This is a toolchain result,
not a camera-channel test.

## Removing a camera OFF argument still leaves the channel absent

Read both the generic channel options and the Android external-build wrapper.
FreeRDP's `channels/rdpecam/ChannelOptions.cmake` defaults the client to OFF,
while its Android `ExternalFreeRDP.cmake` explicitly selects ON. An embedding
that replaces that wrapper must retain the Android ON setting. Check the
actual native CMake cache; absence of an OFF argument does not prove enablement.
Keep a camera-disabled APK as the endpoint control.

## A supported channel appears absent before the first connection

The Android Java class queries camera support while it initializes, before a
session registers its addin provider. `freerdp_load_channel_addin_entry` depends
on that provider. The compiled-table query
`freerdp_channels_load_static_addin_entry` can inspect built-in support at this
point. A native check with the known built-in display-control channel returned
indirect=0, static=1 before a session; an invented channel returned 0. This
checks lookup semantics, not Android camera delivery. Also keep channel
presence separate from optional pixel conversion: raw NV12 passthrough does
not require an NV12-to-I420 converter.

## KRdp cannot find encoderPaused or setEncoderPaused

An otherwise matching Qt/KF SDK can still contain an older KPipeWire API.
Inspect the KRdp commit that introduced backpressure and the KPipeWire public
header. Upstream KPipeWire's `PipeWireBaseEncodedStream` supplies these methods;
they are absent from the packaged 6.7.4 API used in the failed build. Build the
matching upstream dependency into an isolated prefix and pass that prefix and
its `KPipeWire_DIR` to CMake. Do not remove the caller's backpressure to make an
older SDK compile. The recorded dependency source is KDE/kpipewire
`bb838b0371012b99b5c199b7aaf662be319ae5b6`; KRdp subsequently built against that prefix and its two registered tests
passed. This establishes a build/test baseline, not display or pose delivery.

## TLS fixture stalls before a channel can negotiate

Read the client log as well as the server log. In the recorded failed attempt,
the Android client invoked `OnAuthenticate` after selecting TLS, then waited
in the stock credential dialog. The server's later `BIO_do_handshake failed`
was not a camera-channel rejection. A TLS-only, unauthenticated test server
can still need explicit public dummy credentials in this client. The proposed
fixture-URI password addition was not rerun before the resource stop; it is
not a verified fix. Require RDP connection and DVC readiness before calling
a camera-disabled timeout the endpoint red control.
