# Packing the ISO

**For maintainers who build the edition's live and install image:** two ways to pack it, both with SparkyLinux's own packer.

The packer is Sparky Backup Core Stereo (`sparky-backup-core-stereo`), the edition's separately named fork of Paweł's [Sparky Backup Core](https://github.com/sparkylinux/sparky-backup-core).
Its pre-squashfs hook runs the [Lean Code](../../lean-code/SKILL.md) projection, which the edition's ISO requires and general Sparky remastering keeps as an option, off by default (Daniel, 2026-10-09; [the policy](https://github.com/Sparky-OS/sparky-stereo-os-build/blob/main/sparky-os/LEAN-CODE-POLICY.md#scope-and-the-remaster-option)).
The scripts are in `sparky-os/iso-build/` and `sparky-os/vm/` of [the build tree](https://github.com/Sparky-OS/sparky-stereo-os-build).

## From a root file system, in containers (the betas)

`iso-build/build-beta.sh rootfs|pack|all` builds the image the way the betas were built:

- `rootfs` (`rootfs.sh`): the root file system, with SparkyLinux KDE's package set on the day's Debian testing, the edition's metapackages with their Recommends, our stereo kernel with Debian's signed kernel beside it, NVIDIA's userspace with the edition's open modules, the installer and the live system.
- `pack` (`pack.sh`): `sparkybackup-stereo dist` in a chroot of that tree, the way SparkyLinux packs its images on the system itself.
  The staged packages go in; the build's own apt sources, policy and module signing key come out.
  The ISO step packs from an overlay, so the root file system is the same for every pack.
- `LEAN=1` is required for release images. `LEAN=0` is accepted only with `ISO_PURPOSE=benchmark` and a `-nolean-` file name.
- Optional inputs: DKMS modules and a kernel package signed with the edition's Secure Boot key (`SIGNED_MODULES`, `SIGNED_KERNEL`).
- Outputs: the ISO, its sums, its package list and the Lean Code image manifest, sealed with `lean.release seal-iso`. Check it with `lean.release check-iso` before any upload.
- The file name is `ISONAME`, for example `sparky-stereo-os-9-mashtabba-beta2-x86_64.iso`; the menu label is `LABEL`.

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
- The boot menus and `.disk/info` are static files under `/usr/lib/sparkybackup/`: brand them from our package.
- The image carries our kernel, NVIDIA's modules with our patches, and the stereo KDE stack.
