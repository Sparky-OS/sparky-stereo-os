# Qualify a Plasma Mobile Catch receiver in QEMU

The handset is a screen for the PC and can also be a 3D compositor in its own right.
The general receiver and panel-control recipe is in [3D to VR](../../3d-to-vr/SKILL.md).
Use a stock arm64 handset first, then run the same receiver proof with the handset's Stereo KWin build.

## Start a stock arm64 handset

1. Get the published [Mobian sunxi Plasma Mobile image](https://images.mobian.org/sunxi/) and its SHA-256 list and detached signature.
   Check the announced download size and scratch space first.
   Verify the signature with the Debian Mobian archive keyring, then verify the image bytes.
   Retain the signed compressed image and use a fresh writable overlay for each test. [Mobian verification instructions](https://wiki.debian.org/Mobian/Verify)
2. Put QEMU, the desktop rig and the phone in a disposable container with `--network none`.
   For two guests, link their virtual NICs with QEMU's socket backend bound to container loopback and configure a private, two-address subnet without a default route.
   A native desktop rig can use a disposable `veth` pair and relay ordinary Ethernet frames to QEMU's Unix datagram NIC. Use the same two-address subnet and complete packet checksums.
   Use no host forwards. Keep the handset on a software display. Use an explicitly assigned renderer for the native desktop only if its virtual KWin needs a render node for screencasting.
   Install guest client packages from an offline disk built from the guest's own signed apt sources.
3. On an x86-64 host, run `qemu-system-aarch64 -M virt -accel tcg,thread=multi -cpu max` with a matching Debian generic arm64 kernel and disposable initramfs.
   Load virtio PCI and block, ext4, virtio GPU, input and network dependencies in module order.
   Mount the image's root partition and switch to its native init.
   The sunxi image's device-specific boot chain stays on the read-only image.
4. Start with `-device bochs-display` and include the generic kernel's `bochs` DRM module in the initramfs. This produced a 1280×800 Plasma Mobile welcome screen without a host render node.
   Use a Unix QMP socket for `screendump` and a socket-backed serial console, without any GUI on the host.
   Record the start clock, kernel/root readiness, graphical target and first visible Plasma Mobile frame.
   Confirm the process, active session and framebuffer before counting the shell as up.
5. For the Mobian sunxi image, disable the VM's nonexistent USB-gadget jobs and the upstream image's swap and device waits for this disposable session. If the greeter keeps exiting, use greetd's `initial_session` with a fresh runfile and the installed Plasma Mobile desktop entry's D-Bus wrapper. The tested Bochs configuration uses `KWIN_COMPOSE=Q QT_QUICK_BACKEND=software`. Keep graphical provisioning and the phone image in the isolated guest.

## Exercise the existing KDE Connect route

Set the guest's default RDP handler to the stock KRDC executable with fullscreen requested.
Pair the one identified phone and one identified rig over the isolated link.
KDE Connect's daemon `devices(true, false)` query includes reachable peers before pairing. Use its `customDevices` property to name the one guest peer explicitly on an isolated two-address link.
The KDE Connect object's `requestVirtualMonitor` invokes the same action as **Use device as an external monitor**.
Record its acceptance, the new KWin output, the receiving process and the first advancing frame on the phone.
A virtual KWin already has an output before the request, so retain the before and after output names and UUIDs. In authentication-first versions of KRdp, the RDP client starts ahead of the new output. Handle the test server's certificate in the client, then wait for the authenticated session to create its output.

The [upstream KDE Connect plugin](https://github.com/KDE/kdeconnect-kde/blob/master/plugins/virtualmonitor/virtualmonitorplugin.cpp) advertises resolution and scale from its primary screen.
Its receiver dispatches an RDP URL through the configured scheme handler.
The released edition's generic PC path also launches a KRdp process for the requested virtual mode.
The edition's native panel path instead acquires a lease through the existing KRdp owner and returns structured data, including the certificate fingerprint and the panel descriptor.
The independently launched Kirigami Catch frontend has a pin callback and per-eye fitting.
Keep the two calls distinct when reporting results.

The proven stock comparison used Debian KDE Connect 26.08.3 and KRdp 6.7.4 on the virtual PC, with KDE Connect 26.08.3 and KRDC 26.04.0 on the Mobian arm64 guest.
The same test compositor ran OpenGL in virtual-output mode.
It created a 1280×800 output at scale 1 and 60 Hz and delivered a changing two-colour chart fullscreen over H.264.
The source order change reached the screen and failed the left-first classifier.

Use a source with different, changing identifiers in the two eyes.
The swapped control must arrive on screen and fail left-first identity.
A frozen frame with valid labels must fail progress.
For a stereo capture, keep the full side-by-side raster in a PNG with left-first `sTER` and the `.pns` extension.
Open the framebuffer before describing it.
Report end-to-end stage times as measured in the guest rig.
Use a physical device to qualify hardware decoding, lens alignment and continuous pose.

## Share the sources

| Piece | Current source | Reuse |
| --- | --- | --- |
| Panel identity and negotiation | Flat Headset's `PanelDescriptor.kt`, KRdp's panel owner and wire validation | Exchange the certificate SHA-256 identity, name, native pixels, physical size, refresh in mHz, scale, lens ID and split-eye request once. Verify geometry against the active KScreen mode. |
| Link modes | Flat Headset's `HeadsetLink.kt`, KRdp and KPipeWire | Use the native raster and named SBS, half SBS, top-and-bottom and half top-and-bottom modes. Restore each native eye as left-first side by side before output fitting. |
| Lens data | `FittedLensCorrection.kt` with `headset_fitted.frag`; Cardboard `DeviceParams` | Carry the fitted shader constants and decode the viewer QR with the existing Cardboard parser. Apply the transform once in the app on stock Plasma, or once in the compositor for the headset output. |
| Locale strings | Flat Headset's resource catalogues and the KRDC, KDE Connect and KRdp catalogues | Share message keys and translations, including decoder, pairing and sensor failures in ten locales. |
| Waiting scenes | `WaitingScenes.kt` and `headset-waiting/catalog.json` | Reuse the catalogue and its marked media. Show the corresponding still if reduce motion is active. |

## Traps

- **The first HTTPS fetch fails with curl error 77.**
  The minimal tools image has no CA bundle.
  Install `ca-certificates` or point curl at the read-only CA file already mounted for apt.
  The package install succeeded while curl failed because apt was using the mounted CA explicitly.
- **The initramfs assembly finds two BusyBox files.**
  The Debian package includes the program and an initramfs configuration hook with the same basename.
  Copy `usr/bin/busybox` from the extracted package.
  The install error emitted both matches.
- **Depmod cannot find the extracted kernel's module directory.**
  The Debian package stores it under `usr/lib/modules`.
  Add the extracted tree's merged-`/usr` symlink or configure the module directory explicitly.
  The missing path in the depmod error names the expected location.
- **The VM waits for a zram device that never appears.**
  The source image requests zram and the small virtual initramfs lacks its module.
  Disable zram for the test boot, then observe the swap target progressing.
  The serial console logged the missing module and the device start job.
- **Systemd reaches its graphical target but the greeter keeps restarting.**
  The graphical target only confirms its unit transaction.
  Check the greetd journal and framebuffer, then run the installed Plasma Mobile session through greetd on the disposable overlay.
  The virtio GPU lacks the physical phone's device-tree properties. The screenshot showed the missing property and the journal showed the greeter exiting before opening a session.
- **The installed shell starts slowly and the first capture is black.**
  KWin, Xwayland and Plasma Mobile's startup services finish at different times under TCG. Wait for the first visible pixels after the shell service is active. On the Bochs run, the first sample at active shell was black, KScreen showed the connected 1280×800 mode, and the delayed capture showed the first-run screen.
- **QEMU's VirGL startup reports that there is no render node.**
  `egl-headless` needs a DRM render node. A device-free container can use `bochs-display` with the matching guest kernel module. Read QEMU's EGL error separately from the guest's kernel and framebuffer logs.
- **The observer misses a target reported by systemd.**
  The serial status lines insert ANSI colour codes around the target name.
  Strip those codes before matching and keep the original log as evidence.
  The graphical-target line was present in the untouched serial log.
- **A Debian-only published-PC fixture cannot resolve KRdp.**
  The selected KRdp build requires the deb-multimedia epoch of the UPnP library.
  Include the signed multimedia source and keep the edition's packages pinned first.
  The isolated apt solve reported no candidate for the required epoch.
- **The serial log stops partway through the kernel banner.**
  The controller connected to the serial socket without consuming output.
  Drain each socket while the guest writes to it and keep QEMU's serial logfile.
  Both kernels continued when the controller started reading from the socket.
- **The desktop guest reaches a login prompt and the debug shell never appears.**
  A container-export root runs `console-getty.service` on the desktop guest's serial console.
  Give that service a shell override only on the disposable rig disk.
  The serial log identified the getty unit and the prepared disk reached a root prompt.
- **Configuring the phone link fails with `ip: command not found`.**
  The image's minimal installation omits iproute2.
  Include it in the offline apt closure and install that closure before configuring the virtual NIC.
  The virtio driver logged the NIC renaming while the guest script failed on the missing executable.
- **Setting the RDP handler fails with `xdg-mime: No such file or directory`.**
  The image omits xdg-utils.
  Write the test user's `mimeapps.list` directly and refresh KDE's service cache.
  The serial log showed the stock client packages had installed successfully before the handler command failed.
- **KDE Connect exposes its D-Bus name and a query can still time out during startup.**
  Check that the desktop daemon actually answers its `devices` method. A listening socket and a D-Bus name show that startup has reached those registrations. The first-run logs showed the session's autostart service appearing after the explicit early launch.
- **A reachable peer is absent from `kdeconnect-cli --list-available`.**
  That view requires pairing. Query reachable devices with `devices(true, false)` before asking for a pair. In the isolated rig, the PC daemon returned one ID while the paired-only CLI returned zero.
- **A phone pairs and the PC reports that it lacks an RDP client.**
  KDE Connect 25.04.2 advertises `supports_vnc` even after stock KRDC is installed. Use an RDP-capable version of the virtual-monitor plugin on the phone. The release tag and the PC's `lastError` identify the version boundary. [Aleix Pol's RDP change](https://github.com/KDE/kdeconnect-kde/commit/e1bf5239d371d2e650827a4e174fa9c06902245c)
- **The PC reports that KRdp is missing even though the package is installed.**
  The released plugin gives its `krdpserver --help` preflight three seconds. The installed program took 6–11 seconds on the TCG desktop. Run the exact PC packages on the container's native CPU and keep the ARM handset in QEMU. The native Wayland help invocation took under half a second.
- **KWin fails to execute in the native rig container.**
  The edition's executable has `cap_sys_nice` outside the container's capability bounding set. Clear that file capability only in the disposable rig and run KWin as the lab user. `getcap` and the failed `exec` exposed the cause.
- **HTTP reaches the native rig and the KDE Connect peer list stays empty.**
  The published LAN backend drops UDP identity packets sourced from loopback. Give the PC and guest distinct addresses. An isolated `veth` with QEMU's Unix datagram NIC keeps the two addresses visible to the ordinary LAN protocol. The independent HTTP check and the inspected `sender.isLoopback()` branch distinguish the failure from a broken transport. [LAN source](https://github.com/KDE/kdeconnect-kde/blob/v26.04.3/core/backends/lan/lanlinkprovider.cpp)
- **ARP works through a packet relay and TCP stays in `SYN-RECV`.**
  Use `ETH_P_ALL` when binding the packet socket, then disable TX checksum offload on the native veth endpoint. QEMU needs the complete on-wire frame at the Unix datagram socket. The desktop's TCP state and the guest's HTTP 200 after the offload change exposed the difference.
- **The virtual-monitor action launches KRDC and its first connection is refused.**
  Cold start in TCG outlasted the PC's 45-second client window. Start the stock client once on the empty guest desktop and wait for its ready log before timing the end-to-end request. The cold and warm logs show when FreeRDP tried the TCP endpoint.
- **FreeRDP logs a host-key warning while the handset still shows its wallpaper.**
  Each isolated PC session generates a new certificate, and FreeRDP logs the warning before its verification callback. For an automated run, obtain the exact certificate from the rig out of band, verify its digest and put only that certificate in the guest's endpoint-specific FreeRDP trust file. Use a read of the current rig certificate and the client's trace to distinguish a pending verifier from a refusal. [FreeRDP TLS source](https://github.com/FreeRDP/FreeRDP/blob/3.33.1/libfreerdp/crypto/tls.c)
- **RDP authenticates and immediately disconnects before a new KScreen output appears.**
  Run KRdp with a client-side Wayland protocol trace in the disposable PC session and inspect the virtual-output request.
  KWin replied `Unsupported compositing type` when its virtual backend had started with QPainter. Its screencast manager requires OpenGL.
  Provide a render node through the container's configured GPU device interface and verify that the virtual KWin session reports OpenGL.
  If the node has mode 0660, grant its group to the disposable PC test account inside the container. Do not change permission bits on the host node.
  Keep the PC in virtual-output mode and the emulated handset on Bochs. [KWin screencast manager](https://github.com/KDE/kwin/blob/v6.7.4/src/plugins/screencast/screencastmanager.cpp) [KWin virtual backend](https://github.com/KDE/kwin/blob/v6.7.4/src/backends/virtual/virtual_backend.cpp)
- **PipeWire reports `target not found` after the virtual output appeared.**
  Compare KScreen output names before and after the request, and check which output the chart setup disabled.
  In this case the numeric position 1 changed from the baseline to the streamed output. Disabling that position removed the stream and KRdp sent zero frames.
  Place the chart on the negotiated output by disabling the baseline with its name, for example `kscreen-doctor output.Virtual-0.disable`. [KScreen command syntax](https://github.com/KDE/libkscreen/blob/v6.7.4/src/doctor/main.cpp)
- **The published PC removes its virtual output roughly 45 seconds after the listener starts.**
  Inspect the PC build's `phone-throw-virtualmonitor.patch` and the guest stock plugin version.
  The downstream timer clears on its `clientConnected` control packet. The stock phone plugin hands the URL to KRDC and has no matching acknowledgement.
  Preserve that run as a compatibility control. The stock KDE Connect and KRdp pair gives a separate way to exercise the upstream protocol on the same virtual desktop.
  For an edition fix, count the authenticated KRdp session on the generic route and verify the structured acknowledgement separately. [Stock plugin v26.08.3](https://raw.githubusercontent.com/KDE/kdeconnect-kde/v26.08.3/plugins/virtualmonitor/virtualmonitorplugin.cpp)
- **Suppressing late-frame drops still leaves the handset without the chart.**
  The published PC logged 73 late drops in one warm run.
  A diagnostic using the shipped KRdp setting `KRDP_KEEP_LATE_FRAMES=1` reduced that count to zero, and the same deadline still closed the connection before the chart appeared.
  Compare the published route with the upstream KDE Connect and KRdp pair while holding the KWin session, renderer and handset fixture fixed.
  Use the stock comparison to prove display delivery and keep the edition's compatibility failure visible.
- **The staged KWin source reaches the arm64 dependency check and exits before compilation.**
  The studied archive supplies Stereo Policy development libraries for amd64.
  Provision the arm64 build dependency and matching Plasma/Qt stack before retrying.
  The arm64 apt solve and `dpkg-buildpackage -a arm64` identify a missing dependency, which gives no result about the compiler or linker.

## Keep the generic session through the deadline

The stock phone's KDE Connect sends the URL to KRDC. It cannot send the edition's structured `clientConnected` message.
Use the authenticated KRdp backend start on the PC to establish the generic session. The published KRdp creates the backend at the RDP activation state, and a completed screencast startup emits the session-start record.
The listener's readiness probe only establishes that the socket accepts a connection.
Scope the startup record to the child using a fresh, local prefix and a complete Qt message record. Keep the explicit session-ID acknowledgement for a structured panel.
An unclaimed generic server still expires after 45 seconds and reports the reason.

For the installed test, pair the stock phone again, request the monitor, and log KRdp and the KScreen output.
Keep the chart advancing for at least another minute after its first capture.
Pause the chart process so the same image stays visible and the progress check fails. Resume it before reversing the eyes.
Close KRDC, confirm that KWin removes the output, then stop the server from KDE Connect.
Run an unclaimed request and verify that the listener goes away at the deadline.

Run the compatibility check with an installed executable that takes ten seconds to answer, an absent executable, and an installed executable that times out or exits unsuccessfully.
The executable's absence, the duration of a timeout and the nonzero exit code have different meanings.
Check `lastError` on the virtual-monitor interface, which is the value the generic action exposes to the person.

- **A working stock receiver goes dark at 45 seconds.** The old plugin waited for a structured acknowledgement on a generic RDP URL. Compare the KRdp activation and KScreen output timestamps with the plugin deadline. Use the authenticated backend-start record for the generic route. With the fixed package, the H.264 chart was still advancing 110 seconds after the request was accepted. Unclaimed listeners continued to expire.
- **An installed sender is reported missing.** The old three-second compatibility check treated a slow help response as absence. Delay the installed executable's response by ten seconds and read the action's error again. Give a started child 15 seconds, then report its measured timeout or exit status.
- **The build rejects the old LC source's Build-Depends layout.** The six Lean Code tools sit at the end of the last continuation line. Use the catalogue recipe's `--build-depends-at-end` path with multiline parsing and compare it against the signed descriptor's unpacked control file. The default prefix assertion pointed to the older source layout.
- **Source preparation cannot start `dch`.** The build image needs Debian's devscripts for the Lean Code changelog step. The source conversion and patch application had already reached `lean.debian_prepare` when it reported the missing executable.
- **The compiled plugin rejects the record comparison.** KDE Connect compiles with `QT_USE_QSTRINGBUILDER`, so concatenation passed directly into `QByteArray::contains` yields a lazy builder. Materialize the complete record as a `QByteArray` before passing it to the comparison. The native compile exposed this even though the patch applied cleanly.

## Check the authenticated receiver before testing layouts

Install the published arm64 Kirigami Catch and the signed dependency closure on the same guest after the generic stock-client test.
Use the current paired KRdp owner and matching KPipeWire packages on the PC.
Verify the app's Headset:1 advertisement and compare the certificate identity it advertises to the live KDE Connect pair.
The published Catch generates a separate panel certificate. The paired sender requires a matching certificate in its actual pairing store before it can connect or acquire a lease.
Keep both identities intact. With published arm64 KRDC `4:26.04.0-1+stereo3d1+lc1` and staged KRdp `6.7.4-1+stereo3d11`, discovery fetched the real advertisement and reported “Pair this headset with this computer in KDE Connect before connecting.”
The receiver's local Wayland mode was 1280×800 at 74.994 Hz, scale 1. The refusal preceded panel output, changed-pin proof, H.264, all five wire layouts, wrong-eye and frozen-frame controls and normal lease release.
The subsequent milestone supplies the approved KDE Connect receiver handoff and the common panel descriptor before repeating those rows.

- **The long stock test leaves QEMU showing the previous screen.** KScreen's `--dpms show` found the Bochs output off even with the Catch surface mapped. Wake the guest display with `kscreen-doctor --dpms on` before checking Catch. In this disposable fixture, disable automatic locking before starting the guest session.
- **Injected input leaves the visible Catch button idle.** The QEMU screenshots kept the ready label and the guest had no SSDP listener. Launch the unchanged Qt app with accessibility enabled and call its Catch button's AT-SPI action in the guest. The status changed to waiting and the actual UDP 1900 listener appeared.

## Reuse the current KDE Connect pair

Start Catch in the phone's own Plasma Mobile session after both devices have paired.
Use the current KDE Connect session certificate as the Headset:1 identity.
On the receiver, require a TLS client certificate and check it against the live KDE Connect store before sending the panel descriptor or acting on a control message.
On the computer, run KRdp's existing paired discovery and panel owner. The phone's certificate must match the pairing. The RDP client then verifies the separate RDP pin received over that authenticated control connection.
Unpair during a stream and check that the control socket closes, the RDP session ends and the panel output disappears.

Report native pixels, mHz and physical dimensions from the active KScreen output. The native descriptor stays version 1. Each packed link uses version 2 with the same `linkFormat` as Android:

| Link | RDP raster for the fixed 720p links | Unpacking |
| --- | --- | --- |
| `native` | Native panel raster | Split horizontally at the midpoint. |
| `sbs-720` | 2560×720 | Split horizontally into two 1280×720 eyes. |
| `sbs-half-720` | 1280×720 | Split horizontally and restore the eye width in the output fit. |
| `tb-half-720` | 1280×720 | Split vertically and restore the eye height in the output fit. |
| `tb-720` | 1280×1440 | Split vertically into two 1280×720 eyes. |

Use the shared Android link labels when preparing the package catalogues. Verify the installed button and refusal separately from the archive checks. The deliberately wrong pin belongs in a separate fixture executable built with `CATCH_PROOF`. Release packages leave that switch off.

- **A cross build asks to replace the build machine's Perl.** APT resolves unqualified Lean Code tool dependencies for the arm64 target, so `perl:arm64` requests `perl-base:arm64` alongside the conflicting amd64 installation. Check the solver's dependency chain. A native arm64 QEMU build can install the tools required by the unchanged source descriptor.
- **The headless arm64 build guest enters emergency mode with the root filesystem mounted.** A boot built from only the Mobian root partition lacks the image's separate boot partition. The serial log shows the missing device and failed `boot.mount`. Use a disposable root copy, disable the fstab generator for the build, and mount the build inputs explicitly.
- **The archive builder cannot create its offline disk.** `mkfs.ext4` comes from e2fsprogs. Check for it before downloading the SDK. The later device test already needs its own matching QEMU tools and uses the signed offline dependency pack.

- **The configured arm64 build outlasts the serial controller.** The compiler can remain busy after its last printed target. Inspect the compiler or emulator CPU and the next build target before deciding where it stopped. Use a longer build-specific deadline and a separate disk checkpoint after CMake configures the source. Replay the ext4 journal on a disposable copy before reusing the checkpoint.
- **An AArch64 command exits 182 in PRoot.** Direct QEMU user mode printed `arm64` for `dpkg --print-architecture`. Verbose PRoot logged its seccomp acceleration and then exited 182 for the identical command. Set `PROOT_NO_SECCOMP=1` for the disposable PRoot build and repeat `dpkg --print-architecture` before starting CMake.
- **The compiler runs much slower than the Qt code generators under emulation.** Keep the native arm64 sysroot and run the signed Debian amd64-host AArch64 compiler through CMake's C++ compiler launcher. Compile a known translation unit and confirm `Machine: AArch64` with `readelf -h` before letting it compile the tree. Record both compiler versions and the source descriptor hash across the transfer to the native package build.

Use the FreeRDP graphics client's surface creation record to check the received raster. An AVC wire update then gives the received codec, and the marked capture gives the eyes, layout and margins. Check the same chart with a deliberately frozen frame, reversed eye order and unequal margins before crediting the positive captures. [FreeRDP graphics client](https://github.com/FreeRDP/FreeRDP/blob/3.33.1/channels/rdpgfx/client/rdpgfx_main.c)


- **The imported CMake tree recompiles at the start of packaging.** The native binary sequence reconfigured the imported tree and requested C++ compilation again.
  Finish the build first and verify its source descriptor digest, release cache and AArch64 executable in the native guest.
  Run the package's configured test target, then use Debhelper's completed-build stamp to proceed through normal binary packaging, dependency resolution and Lean Code.
  The native logs distinguish the first repeated C++ compile from the successful packaging run.
- **The Catch dropdown has only `SetFocus` in AT-SPI or ignores the QEMU input event.** Use the proof rig's Wayland client in the disposable handset session and get the chooser geometry from AT-SPI.
  Click to open the popup, invoke `Press` on the menu item with the intended translated label, then read the chooser value back.
  The accessibility probe showed the `Press` action on the open menu item and the updated value after activation.
- **The changed-pin fixture reports a JSON syntax error on `{`.** Its descriptor is formatted across lines.
  Decode the complete document beginning at the opening brace and compare it with the handset's native KScreen values before starting the connection.

Keep compositor input permissions scoped to the test handset session. [Stereo proof rig](../../stereo-proof-rig/SKILL.md)

On the weekly Mobian arm64 fixture dated 2026-11-22, the paired native Catch reproduced `1280×800`, `74994` mHz, scale `1` and `325×203` mm on the PC output.
FreeRDP reported an AVC update to a `1280×800` surface.
The marked native image held both eyes, and the frozen, reversed and unequal controls each failed their corresponding positive picture check.
The wrong pin refused RDP after mutual control identity was accepted, and the paired desktop output disappeared when Catch closed.

For the four packed links, the PC capture stayed `2560×720`, and the received surfaces matched the four advertised sizes in the table.
The receiver restored equal fitted margins in both eyes.
Removing the KDE Connect pair while RDP was receiving AVC revoked the active output lease.

- **The change detector reports progress while the chart marker has still to appear.** A whole-frame inequality can count unrelated pixels.
  Sample both eyes at locations predicted by the chart marker and wait for the requested marker before timing the frozen interval.
  The rejected capture had the same marker values as the baseline, while the actual progress and freeze captures had the bright value in both eyes.



## Measure eye margins at full resolution

The paired rig's `equal_eye_margins` samples every fourth pixel and allows 8 pixels either way, so it printed `0, 0, 3, 3` for a picture that reaches the edge (the last sample sits three pixels short), and a real margin of up to 8 pixels would pass (row 124, main session's review, 2026-11-26).
Read every pixel of both eyes: the five links measured `0, 0, 0, 0` (native) and `0, 220, 0, 220` (each packed link on a 1280x800 panel) in both eyes.
A colour threshold also moves with the encoder: one rerun read `4, 222, 4, 222` for `tb-half-720`, equal in both eyes, where the others read `0, 220, 0, 220`, because a compressed half-height frame blurs the colour edge.
So a margin check with tolerance 0 measures geometry the chart places and H.264 keeps (marks, the marker), never where a colour fades.

## A second Throw that gets no picture

KPipeWire on the PC can answer a second Throw in one KWin session with "Stream error: no more input formats" and "PipeWire remote error: -32 no more input formats" after KRdp's "Video stream initialized with H.264 enabled"; the phone then shows nothing and Catch says nothing (queue row 927, seen in row 924's and row 124's reruns on 2026-11-26).
A red row with this line in the PC log is that fault, not the receiver: read `*-pc.log` before blaming Catch.

### Check the format list and first picture

- **Symptom.** KRdp selects H.264, then KPipeWire reports `no more input formats` and the phone stays on its waiting view.
- **Cause.** The 6.7.4 KPipeWire source builds the PipeWire format parameters into 4,096 bytes. NVIDIA's DMA-BUF modifier lists can require more space. The builder reports its full required size, but returns null for objects that cannot fit. KPipeWire removes those objects. If the omitted objects include BGRx and BGRA, the producer and consumer cannot agree on a format.
- **Fix.** Carry Zhongli Wu's upstream buffer-resizing change and keep the packaged release's `buildFormat` signature. Rebuild the complete list into the grown buffer before publishing it, including on renegotiation. [KDE bug 524881](https://bugs.kde.org/show_bug.cgi?id=524881) · [KPipeWire change](https://invent.kde.org/plasma/kpipewire/-/commit/71ba11ff887c6eb900b5541b4a8d7bf74bd3ae28)
- **How the format loss was measured.** Compile the exact packaged builder against PipeWire's headers. Put BGRx and BGRA last, run a no-modifier control with nine offers, then add 13 modifiers to each format at 74,994 mHz. The requested buffer reaches 5,328 bytes. The published +8 and staged +9 submitted 13 objects with neither BGRx nor BGRA. The backport submitted all 18 including two offers for each of those formats. This control proves the capacity and ordering fault using an explicit offer list. Count actual RDP failures separately.
- **How to trace a running stream.** Record the input format objects as the KRdp process calls `pw_stream_connect` and `pw_stream_update_params`. Log object sizes, format names and modifier counts. Compare the offer with KWin's format list and the first received AVC frame. Reuse the compositor for repeated Throws, label each link and count all attempts. A shell or desktop startup failure belongs outside that count.

The installed package replay used one virtual KWin session and eight circuits through native, full side by side, half side by side, half top-and-bottom and full top-and-bottom. A pinned FreeRDP client on the private loopback recorded the first AVC update. Published +8 failed negotiation 5 times in 40 and staged +9 failed 3 times in 40. The +11 backport sent AVC on all 40 attempts with the same KRdp +11 server used in the staged run. In the actual red trace neither BGRx nor BGRA was present. Each long modifier list carried 14 values including the repeated default.

The KRDC controller's first-picture timer starts after the approved RDP session starts and stops on the first decoded image. On expiry the app closes its listener, releases the session and tells the person to start the Throw again. The final control message goes over the still-paired TLS connection. The desktop discovery client accepts it while the approved lease is active and uses the same sentence in its notification. The package catalogues carry the same sentence in the edition's languages.

For the installed timeout control, keep the RDP graphics negotiation and pairing active and withhold the PipeWire producer in the disposable PC.
Check that KRdp selected H.264, Catch exposes the message without another button press, and the private Plasma notification service receives the same message.
Check that the virtual output disappears and Catch stops advertising after the deadline.
Run the five positive links on the same desktop to verify that a decoded picture cancels the timer.

- **The notice test stops before RDP and Plasma logs `starting invalid corona`.** The minimal PC rig has Plasma Workspace without the desktop shell assets. Add `plasma-desktop` and use the private Wayland environment for D-Bus activation. Check `GetServerInformation` on `org.freedesktop.Notifications` before arming Catch. The repaired fixture reported Plasma 6.7.4 and protocol 1.2.
- **The notification daemon is present and the applet's PulseAudio QML import fails.** The default Plasma notification applet imports `org.kde.plasma.private.volume`. Install the matching `plasma-pa` package inside the fixture. The shell log named the missing module and the package installed its `qmldir`. Keep the KPipeWire QML package at the same version as its exact-version libraries.

### Keep an offline guest installation

- **Symptom.** The serial fixture times out during package installation under load.
- **Cause.** A timed-out serial reader leaves the installation running. In one run the shell later printed the expected package versions and its successful exit marker.
- **Fix.** Wait for a successful `dpkg --audit` and `sync` in the isolated guest. Pause QEMU, copy its guest-only QCOW2 overlay and resume QEMU. Save the overlay checksum. Use a throwaway child overlay with the same verified distribution image as its backing file for the next boot.
- **How found.** The end of the serial log showed the original command exiting zero after the host timed out. The checkpoint proof reran the package query and confirmed KRDC, KDE Connect, Plasma Mobile and KWin versions before the copy.

- **The session has a working private link and a black framebuffer before pairing.** Read the phone's user journal for the Plasma startup services. In the loaded QEMU run, `plasma-kded6` and `plasma-ksmserver` hit their 90-second startup limits just before the shell started. Give the disposable TCG guest's user services more startup time and then recheck a visible shell. Keep the production first-picture deadline tied to RDP approval.
- **The full-system arm64 C++ build advances slowly after configuration.** Preserve a guest-only configured root. If the copy was taken while QEMU was paused, repair a disposable copy with `e2fsck` before reuse. Build the unchanged source with the guest's headers and an AArch64 cross compiler. Verify the source descriptor, an AArch64 ELF and `CATCH_PROOF=OFF` before importing the objects into the native package step. The compiler and descriptor records distinguish the release build from the separate wrong-pin executable.

## Credits

The KDE Connect virtual-monitor source names Aleix Pol i Gonzalez and Fabian Arndt, and the downstream protocol-v2 history names Fabian Druschke.
Zhongli Wu authored the upstream format-buffer fix.
Arjen Hiemstra developed KRdp and KRDC's FreeRDP session.
KRDC's RDP view credits Arend van Beelen jr., Urs Wolfer and AceLan Kao.
Plasma Mobile's startup file names Aleix Pol, Bhushan Shah and Jonah Brüchert.
The FreeRDP H.264 backend names Marc-André Moreau and Mike McDonald.
The receiver also builds on Bastien Nocera's iio-sensor-proxy, the Mobian team and Fabrice Bellard and the QEMU contributors.

## Verify the Flat Headset presentation

Build the renderer against the same recorded Flat Headset source as the handset. For the fitted Shinecon profile, compare every rendered pixel with Android's original fragment shader under software EGL and exercise both orientations of the source texture. Repeat at the rig's panel raster and at two wider display rasters.

For a viewer QR profile, parse the full Cardboard `DeviceParams` URL and derive the projection from the screen's actual physical width and height. Compare the software rasterizer with GLES drawing the corresponding Cardboard mesh. Cover the blocked areas as well as the visible pixels. For uncorrected, compare input and output bytes. Counterchecks use a different viewer's data, a changed fitted coefficient and optical correction before fitting.

Fit the two full eyes into equal panel halves. Apply optics to the fitted panel, and clamp each optical sample to its own eye. Apply the same camera-cutout mask to each edge of each eye and draw the centre line and arrow on top. Keep the display guide out of the fit comparison. The guide should remain straight under both optical profiles.

Encode a chart with solid marks using H.264 under the actual wire dimensions. Ask the decoder for its pixels and predict the destination rectangles independently for both eyes. Compare the entire output with tolerance zero. Shift one eye by a single pixel and mask one extra edge pixel in separate controls. The larger boundary heuristic from a live colour-gradient chart is useful to bring up the rig. The encoded comparison is the geometric gate.

Read the Android waiting catalogue and use its named local files. Require PNG `sTER` mode 1 for the still and left-first side-by-side stereo metadata for the movie. Motion uses the hardware-only branch, and Reduce motion selects the still directly. Check separate connecting and reconnect clips, loop restart and the first desktop frame ending the wait. The original `e90e0194` release catalogue is empty. The Android debug scene files provide marked inputs without manufacturing production artwork.

### Traps from the presentation proof

- **The Cardboard comparison rejects four pixels.** The inclusive software triangles and GLES use different ownership at a raster edge. Inspect the coordinates and require all disagreements in coverage within one pixel of that edge. Keep the one-level RGB bound on every pixel covered by both renderers. Keep the full-resolution fit comparison exact.
- **The H.264 file decodes no frame and FFmpeg reports “File exists”.** The original chart command declared stereo both in Matroska and the H.264 packing SEI. On the tested FFmpeg 9 graph the two marks collide. The chart only needs one mark, so declare it once through Matroska stream metadata. Confirm the single left-first side datum with ffprobe before running the pixel checks.
- **The standalone renderer proof passes and the Catch app fails to compile.** The KDE project applies `-fno-exceptions`. The carried profile parser and Cardboard inverse rejection use exceptions on invalid data. Enable exceptions on those C++ source files and the one caller that catches the error. Rebuild the actual Catch target with `WITH_CATCH=ON`.
- **A decoder error arrives even though the scene has the correct stereo mark.** The isolated rig provides no video-decoder device. Confirm the decoded still and that the marked clip reaches the hardware availability check. Use an explicitly injected proof decoder to measure loop behavior in a disposable process. The release should explain the missing hardware without picking the still automatically.
- **The locale patch applies to the earlier reference folder and fails when quilt reapplies the accepted source.** The row 927 source ends each catalogue with the first-picture notice. Use that appended message as context and verify all nine translated catalogues with `msgfmt -c` after extracting the exact new descriptor.

- **The AArch64 build aborts in the Catch automatic MOC step with allocator corruption.** The raw user-mode SDK configured and built the RDP session first. The failure was in its code-generation phase. Verify the exact Qt tools package version on both architectures and run matching host `moc` and `rcc` for generation. Keep ARM libraries and headers in the signed SDK. Verify that `readelf` identifies the linked executable as AArch64 and that its source descriptor hash matches the other architecture's. This qualifies the executable build. The distribution package still has its own native Lean Code and payload gates.

### Locate a live capability error

An unavailable decoder for a local waiting clip and an unavailable decoder for an approved Throw are different events.
Check the active transport's decoder for the approved codec.
FreeRDP's H.264 context constructor initializes its backend and can return null before the receiver starts.
The current paired offer carries the panel, NLA endpoint and certificate fingerprint.
The head-fixed Flat Headset path runs without continuous pose.
When a mode explicitly requires pose, a Qt Sensors connection is only a backend check.
Confirm that it starts and supplies a first reading within the mode's deadline. [FreeRDP H.264 backend](https://github.com/FreeRDP/FreeRDP/blob/3.33.1/libfreerdp/codec/h264.c#L842-L951) [Qt Sensors lifecycle](https://doc.qt.io/qt-6/qsensor.html#start)
