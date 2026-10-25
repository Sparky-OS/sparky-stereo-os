# Packing the ISO

**For maintainers who build the edition's live and install image:** two ways to pack it, both with SparkyLinux's own packer.

The packer is Sparky Backup Core Stereo (`sparky-backup-core-stereo`), the edition's separately named fork of Paweł's [Sparky Backup Core](https://github.com/sparkylinux/sparky-backup-core).
Its pre-squashfs hook runs the [Lean Code](../../lean-code/SKILL.md) projection, which the edition's ISO requires and general Sparky remastering keeps as an option, off by default (Daniel, 2026-10-09; [the policy](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/LEAN-CODE-POLICY.md#scope-and-the-remaster-option)).
The scripts are in `sparky-os/iso-build/` and `sparky-os/vm/` of [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build).

## From a root file system, in containers (the betas and the developer ISO)

`iso-build/build-beta.sh rootfs|pack|check|all` builds the image the way the betas and the developer ISO were built:

- `rootfs` (`rootfs.sh`): the root file system, with SparkyLinux KDE's package set on the day's Debian testing, the edition's metapackages with their Recommends, the edition's kernel and no other, NVIDIA's userspace with the edition's open modules (through `sparky-stereo-nvidia-driver-lock`, installed first, which keeps the driver at the module's version), the installer and the live system.
  Debian's kernel is not shipped (Daniel, 2026-10-24: it has no stereo 3D); a pin keeps every Debian kernel package out while the tree is built, and `boot-kernels.py` stops the build if one is in `/boot` or installed.
- `pack` (`pack.sh`): `sparkybackup-stereo dist` in a chroot of that tree, the way SparkyLinux packs its images on the system itself.
  The staged packages go in; the build's own apt sources, policy and module signing key come out.
  The ISO step packs from an overlay, so the root file system is the same for every pack.
- `check` (`check-iso.sh`): the packed ISO against the recipe, with the ISO mounted read-only: one live kernel, signed with the edition's key; the menus, with no second kernel and with the Secure Boot enrolment in the nine languages; the EFI image's shim, GRUB and MokManager, the same files as the root file system's packages, and the edition's certificate; the image's `/boot`; the boot splash in the image and in the live boot image; command-not-found's index.
- `EDITION_REPO`: `live` (the default) reads the published repository at https://repo.sparkyos.org/, so the image is what people get; `flat` reads the development repository (`REPO`).
- `ADD_HOSTS`: `host:address` pairs for the containers (`docker run --add-host`), for a repository host that the containers reach only on the local network.
- `LEAN=1` is required for release images. `LEAN=0` is accepted only with `ISO_PURPOSE=benchmark` and a `-nolean-` file name.
- Optional inputs: DKMS modules and a kernel package signed with the edition's Secure Boot key (`SIGNED_MODULES`, `SIGNED_KERNEL`), and the edition's public certificate for the EFI image (`MOKCERT_FILE`; default: the packer package's copy).
- Outputs: the ISO, its sums, its package list and the Lean Code image manifest, sealed with `lean.release seal-iso`. Check it with `lean.release check-iso` before any upload.
- The file name is `ISONAME`, for example `sparky-stereo-os-9-mashtabba-dev-20261025-x86_64.iso`; the menu label is `LABEL`.

## The boot menus and Secure Boot

`sparkybackup-stereo` writes the boot menus at every run from what the image and the medium hold (`stereo/gen-menus.py` in the packer): the default live kernel (`LIVEKERNEL`) and every further kernel in `/boot`, each with its entry; the languages of the base menus, with each locale's keyboard layout (`stereo/keyboard-layouts`), and `LIVELANGUAGES` on the first page; the Secure Boot enrolment when MokManager and the certificate are on the EFI image.
Nothing in the menus is written by hand.

The chain under Secure Boot is Debian's Microsoft-signed shim, Debian's signed GRUB, and the edition's kernel signed with the edition's key, which shim accepts once the key is in the firmware's MOK list:

- On the live medium, a kernel shim refuses ("bad shim loader signature") leads to an explanation in the nine required languages and to the menu again with "Secure Boot: enroll the Sparky Stereo OS key" selected; that entry shows the steps in the nine languages and starts MokManager.
- In MokManager: Enroll key from disk, the disk, EFI, boot, `sparky-stereo-secureboot-2026.der`, Continue, Yes, Reboot. Enrolling from disk asks for a confirmation and no password; the one-time password belongs to `mokutil --import` from a running system.
- On an installed system, `sparky-stereo-boot` keeps the certificate next to every shim on the EFI system partition and puts the same entry in GRUB's menu, in the system's language; under Secure Boot, when shim refuses the newest kernel, the entry is the menu's default. A new or reset motherboard, or Secure Boot turned on after the installation, ends at the enrolment, never at a dead end.

## Proving an image

`iso-build/boot-matrix/` boots an ISO headless in QEMU (`-display none`, screenshots through QMP), under SeaBIOS, OVMF with and without Secure Boot, and 32-bit OVMF:

- `live-check.py`: boots through the firmware and the medium's own menu, can add the serial console to the selected GRUB entry, logs in on the serial line and runs `checks/live.txt`; screenshots of the menu, the edited entry and the desktop.
- `installed.sh` and `disk-tool.sh`: an installed disk with a serial login (`getty`), its EFI files (`fallback`) and its kernels (`kernels`); `checks/installed.txt` on the serial line.
- `bootmatrix.py` and `vmctl.py`: one boot with a key timeline, and single keys or screenshots for walking through MokManager.

## From the running development VM

SparkyLinux packs an image from the running, customised system, and the edition can pack its development VM the same way (`vm/sparky-vm.sh`, provisioned by `vm/provision.sh`).

- The running kernel becomes the ISO's kernel: boot the VM on our stereo kernel before packing.
- Before packing, run `vm/prepack.sh` (the command-not-found index, BleachBit without localizations, TRIM).
  Right before sparkybackup, run `vm/prepack.sh --final`: it removes passwordless sudo, the `file:` repository and the SSH server, and resets the machine-id.
- Paweł names his images `sparkylinux-YYYY.MM-x86_64-<edition>.iso`, beside `<iso>.allsums.txt` and `<iso>.package-list.txt`.

## In both

- `sparkybackup skel` copies only a hard-coded list of dotfiles into `/etc/skel`; anything else reaches `/etc/skel` from a package.
- Kernel parameters for the installed system go in `NewGrubDefLine` (`/etc/sparkybackup/sparkylinux-installer.conf`).
- Sparkybackup takes its label from keywords grepped in `/etc/sparkybackup/sparkybackup.conf`, and "stereo" matches none.
  So the edition's packer writes the label and the file name into `sparkybackup-stereo.conf` (`ISOLABELFULL`, `CUSTOMISO`).
- The boot pictures and the menu texts are under `/usr/lib/sparkybackup/stereo/`; the menus themselves are written at every run.
- The image carries the edition's kernel and no other, NVIDIA's modules with our patches, and the stereo KDE stack.
