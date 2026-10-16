# Sparky Stereo OS 9 Mashtabba beta 1: a technical field guide

You can inspect the tested boot path, install layout, package sources and stereo display contract in a beta 1 image built on Debian 14 Forky and KDE Plasma 6.7.
This guide records the image's current behavior and the limits that matter when you evaluate it.

Sparky Stereo OS, Daniel Ramos's edition of SparkyLinux (by Paweł "pavroo" Pijanowski)

## Image and checksums

The image is sparky-stereo-os-9-mashtabba-beta1-x86_64.iso; the download link goes to beta testers: ask for it in the [beta tester thread](https://github.com/Sparky-OS/sparky-stereo-os/issues/26).
The image is 5,166,120,960 bytes, about 5.2 GB, and needs a USB stick of at least 8 GB.

SHA-256: `3564fc23315117bb552543235e889e5a398c9cf13e41ec0cceb6086ff43a25ab`.
SHA-512: `cd7c3da5ae699b951471a4c9d6e7443f5a8944fd7eb3a0f2f7d311c96275689be1e056c0ea96296f4ffd75ba4c3b21a5d79c499bb8a34e43b7d89784a35bd377`.

On Windows, run `certutil -hashfile <file> SHA256` and compare its output with the SHA-256 above.
On Linux, run `sha256sum <file>` and compare its output with the same value.

## Boot chain and tested matrix

With Secure Boot enabled, firmware starts Debian's signed shim, which starts Debian's signed GRUB.
GRUB starts the edition's kernel, `7.3.0-rc6-stereo3d8`, only after the edition's Machine Owner Key is enrolled.
If that key is not enrolled, the image falls back to Debian's signed kernel, which boots without the edition's stereo kernel features.
After enrollment, the signed edition kernel and signed modules such as `acpi_call` and `evdi` load under Secure Boot.

The certificate is `EFI/boot/sparky-stereo-secureboot-2026.der` on the image.
MokManager displays this SHA-1 fingerprint: `02:56:F3:3B:33:F4:68:9A:31:27:0E:8A:AF:9F:13:B4:4D:8B:46:D7`.
The same key can be queued from the live session with `sudo mokutil --import /usr/lib/sparkybackup/stereo/secureboot/sparky-stereo-secureboot-2026.der`, then confirmed in MokManager after reboot.
MokManager's first “Press any key” prompt times out after about 10 seconds, so press a key as soon as it appears.

![UEFI boot menu from the beta 1 USB image](images/beta1/boot-menu-uefi.jpg)
![MokManager selecting the edition certificate from the USB image](images/beta1/mok-disk-5-file.png)

The VM matrix reached the desktop in 12 of 14 cases.
SeaBIOS legacy BIOS and OVMF UEFI booted from both CD and a USB written with `dd`.
Secure Boot also booted from both media with the default test state, the 2024 SBAT level, 2011 Microsoft CA only, and 2023 Microsoft CA only.
The ia32 32-bit UEFI case did not boot from either medium.
The VM host was heavily loaded, so its boot times are not a measure of real hardware.

## Installer and disk behavior

Calamares uses one system partition, with the EFI system partition shared when installing beside Windows.
The tested dual-boot path shrinks Windows first, then chooses “Replace a partition” and the free space in the installer.
The installer leaves Windows' fallback loader byte-for-byte unchanged, lists “Sparky Stereo OS GNU/Linux” and “Windows Boot Manager” in GRUB, and keeps the hardware clock in local time for Windows.
“Install alongside” shrinks a partition from inside the installer; the tested path instead creates unformatted space in Windows before installation.
The install works offline because GRUB's EFI packages are on the image.

![Installer partition choice for the free space beside Windows](images/beta1/installer-replace-free-space.jpg)

The standalone “Erase disk” path was also proven offline under Secure Boot.
Its installed disk boots through the firmware fallback path at `EFI/boot/BOOTX64.EFI`, with shim, GRUB, MokManager and `grub.cfg` beside it.

## APT sources, pins and Lean Code manifest

The installed system retains APT sources for Debian, SparkyLinux, deb-multimedia and the edition's own repository, in `/etc/apt/sources.list.d/sparky-stereo.sources` and `/etc/apt/sources.list.d/sparky-stereo-deb-multimedia.sources`.
The edition repository is not online yet, so APT reports that source as unreachable while Debian, SparkyLinux and deb-multimedia updates work.
The preferences in `/etc/apt/preferences.d/sparky-stereo` assign priority `1001` to every package from origin `Sparky Stereo OS`, so an update does not replace the stereo stack with stock packages.
The generated “only ours” list in `/etc/apt/preferences.d/sparky-stereo-only-ours` pins the stack packages from origins `Debian` and `Unofficial Multimedia Packages` to `-1`, leaving the edition builds as candidates.
Bino is available only from the edition because Debian's and deb-multimedia's Bino packages are pinned to `-1`; their own output modes would hand KWin a picture outside the full side-by-side contract.
The edition's `deb-multimedia-keyring` package has priority `400` as the way into that repository.

The image build output includes `sparky-stereo-os-9-mashtabba-beta1-x86_64.iso.lean-code-manifest.tsv.xz` beside the ISO.
Its columns are `path`, `format`, `bytes`, `comment_bytes` and `projected`.
The manifest inventories comment-bearing files, their sizes and the number of comment bytes in each.
`projected` says whether a file was replaced on the image by its lean projection, which is the same file with its comments moved out to the documentation.
In beta 1 all 49,256 rows say `no`, so no file is projected yet.

## Stereo stack in this image

The display path uses the kernel, Mesa, KWin, Xwayland, Qt and FFmpeg as one contract: programs hand the compositor full side by side, left eye first, and KWin converts that image for each output.
The package versions below are the versions recorded in the beta 1 image package list.

- Kernel: `linux-image-7.3.0-rc6-stereo3d8` (package version `7.3.0~rc6-8`) is the edition's signed kernel, with the edition's patches for HDMI 3D modes.
- Mesa: `26.1.6-1+stereo3d13` packs quad-buffer OpenGL and two-layer Vulkan output into full side by side and declares it for the compositor.
- KWin: `4:6.7.4-2+stereo3d26` consumes full side by side and applies the selected output format per screen.
- Xwayland: `2:24.1.13-1+stereo3d2` is the edition's build for stereo X11 windows on the Wayland desktop.
- Qt: the image carries `qt6-base 6.11.2+dfsg-5+stereo3d6` from the public [`stereo3d-6.11` branch](https://github.com/Sparky-OS/qtbase/tree/stereo3d-6.11).
  Its 15 October 2026 change keeps Qt's viewport and fractional scale objects for a stereo Wayland window because, with version 2 of the KDE stereo content declaration, the compositor takes a full side-by-side surface's size as one eye.
  Qt Wayland EGL windows ask for two views with `EGL_EXT_multiview_window`.
- FFmpeg: `10:9.0.2-dmo1+stereo3d3`, deb-multimedia's FFmpeg with the edition's patches, carries the edition's 3D signals; the public upstream-status page lists the H.264 and H.265 decoder changes as in review, not merged.

The format contract and division between programs and outputs are documented in [How it works](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/how-it-works.md).
The status of fixes sent to other projects, including the FFmpeg items still in review, is in [Upstream merges](https://github.com/Sparky-OS/sparky-stereo-os/blob/main/docs/upstream-merges.md).

## Reporting a useful result

File reports in [issue #26, in English](https://github.com/Sparky-OS/sparky-stereo-os/issues/26).
Include the hardware model and display connection, the exact boot or display steps, the expected result and the observed result.
Attach `cat /etc/os-release`, `uname -r`, `mokutil --sb-state`, `inxi -Fxz`, `stereo-display-info`, and `kscreen-doctor -o` output when relevant.
Attach `drm_info` output if `drm_info` is installed.
For a boot or system issue, attach `journalctl -b -p warning --no-pager` output.
For a Calamares issue, copy `/root/.cache/calamares/session.log` before restarting the live session, because that session does not keep the log after restart.
Include a screenshot or a photo for problems in firmware, the boot menu or MokManager.

## Known beta 1 issues

Machines with 32-bit UEFI, mostly older Atom tablets, do not boot this image.
MokManager's first “Press any key” screen times out after about 10 seconds.
The installer slides are in English even when the installer is set to German or another language.
The GRUB menus still show SparkyLinux's blue atom, Quick Settings still offers Breeze and Breeze Dark, and KDE's Welcome Center opens beside Sparky Welcome at first login.
The edition's own package repository is not online yet, so APT reports that source as unreachable while Debian, SparkyLinux and deb-multimedia updates work.
A live USB is slower than an installed system.
