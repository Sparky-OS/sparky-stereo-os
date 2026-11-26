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
   Leave out host forwards and host render nodes.
   Install guest client packages from an offline disk built from the guest's own signed apt sources.
3. On an x86-64 host, run `qemu-system-aarch64 -M virt -accel tcg,thread=multi -cpu max` with a matching Debian generic arm64 kernel and disposable initramfs.
   Load virtio PCI and block, ext4, virtio GPU, input and network dependencies in module order.
   Mount the image's root partition and switch to its native init.
   The sunxi image's device-specific boot chain stays on the read-only image.
4. The initial display device is `-device virtio-gpu-pci`.
   Use a Unix QMP socket for `screendump` and a socket-backed serial console, without any GUI on the host.
   Record the start clock, kernel/root readiness, graphical target and first visible Plasma Mobile frame.
   Confirm the process, active session and framebuffer before counting the shell as up.
5. For the Mobian sunxi image, disable the VM's nonexistent USB-gadget jobs and the upstream image's swap and device waits for this disposable session. If the greeter keeps exiting, use greetd's `initial_session` with a fresh runfile and the installed Plasma Mobile desktop entry's D-Bus wrapper. The virtual GPU worked with `KWIN_COMPOSE=Q QT_QUICK_BACKEND=software`. Keep graphical provisioning and the phone image in the isolated guest.

## Exercise the existing KDE Connect route

Set the guest's default RDP handler to the stock KRDC executable with fullscreen requested.
Pair the one identified phone and one identified rig over the isolated link.
The KDE Connect object's `requestVirtualMonitor` invokes the same action as **Use device as an external monitor**.
Record its acceptance, the new KWin output, the receiving process and the first advancing frame on the phone.
A virtual KWin already has an output before the request, so retain the before and after output IDs. In authentication-first versions of KRdp, the RDP client starts ahead of the new output. Handle the test server's certificate in the client, then wait for the authenticated session to create its output.

The [upstream KDE Connect plugin](https://github.com/KDE/kdeconnect-kde/blob/master/plugins/virtualmonitor/virtualmonitorplugin.cpp) advertises resolution and scale from its primary screen.
Its receiver dispatches an RDP URL through the configured scheme handler.
The released edition's generic PC path also launches a KRdp process for the requested virtual mode.
The edition's native panel path instead acquires a lease through the existing KRdp owner and returns structured data, including the certificate fingerprint and the panel descriptor.
The independently launched Kirigami Catch frontend has a pin callback and per-eye fitting.
Keep the two calls distinct when reporting results.

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
  KWin, the Xwayland software fallback and the Plasma Mobile startup services finish at different times under TCG. Use the installed desktop entry's D-Bus wrapper, KWin QPainter and Qt Quick's software backend, then check the active shell and a complete frame. The serial samples showed KWin starting before Xwayland, the Plasma service starting near 2½ minutes, and the first framebuffer still black at that point.
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
- **The staged KWin source reaches the arm64 dependency check and exits before compilation.**
  The studied archive supplies Stereo Policy development libraries for amd64.
  Provision the arm64 build dependency and matching Plasma/Qt stack before retrying.
  The arm64 apt solve and `dpkg-buildpackage -a arm64` identify a missing dependency, which gives no result about the compiler or linker.

## Credits

The KDE Connect virtual-monitor source names Aleix Pol i Gonzalez and Fabian Arndt, and the downstream protocol-v2 history names Fabian Druschke.
Arjen Hiemstra developed KRdp and KRDC's FreeRDP session.
KRDC's RDP view credits Arend van Beelen jr., Urs Wolfer and AceLan Kao.
Plasma Mobile's startup file names Aleix Pol, Bhushan Shah and Jonah Brüchert.
The FreeRDP H.264 backend names Marc-André Moreau and Mike McDonald.
The receiver also builds on Bastien Nocera's iio-sensor-proxy, the Mobian team and Fabrice Bellard and the QEMU contributors.
