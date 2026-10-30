---
metadata:
  requires-packages: systemd
name: system-housekeeping
description: >-
  Maintain bounded logs, kernel retention and cleanup policy while preserving user settings, boot recovery and diagnostic evidence.
---

# System housekeeping

## Working recipe

1. Identify package ownership, running and fallback kernels, disk consumers and the diagnostic material needed before removal.
2. Simulate the specific package transaction, inspect dependencies and preserve one useful crash trace; use an isolated fixture for automatic policy.
3. Return the reviewed removal set and recovery evidence. Never substitute broad autoremove for the kernel-only policy.

**Check freshness first.**
Written on 2026-10-07; old kernels and the boot chain revised on 2026-10-30.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

Daniel's rule: "we don't grow so fast, and when grow self prune".
A user's disk must not creep up because Linux keeps everything.

## Old kernels

Daniel, 2026-10-30: "cap to 2 - current and one previous as I said (this is a must to the final user!)".

- **When:** right after a new kernel has installed successfully, meaning its image, its boot image and its GRUB entry were written. A failed install never removes anything.
- **What stays, per kernel flavour:** the running kernel and the newest. If the newest is the running one, the one before it. Never fewer than one, never the running one. That is apt's own rule (`APT::NeverAutoRemove::KernelCount`, default 2).
- **What goes:** that release's kernel packages only, purged: image, binary, modules, headers, the per-release base package, their `-dbg` and Lean Code `-lc-hr` companions, and the per-version kbuild and headers-common packages that no remaining package needs. Then its `/lib/modules/<release>` folder when no package owns it and no `/boot/vmlinuz-<release>` exists, its DKMS records, and every kept kernel's boot image and GRUB's menu written again.
- **Debian's kernels are split** (forky: `linux-image`, `linux-binary`, `linux-modules`, `linux-base` and `linux-headers` per release, `linux-kbuild` and `linux-headers-<version>-common` per version). Purging `linux-image` alone leaves the kernel, its modules and its GRUB entry. `linux-base-amd64` is a dummy that pulls Debian's kernels back.
- **Check the transaction first:** `apt-get -s purge` with exactly the computed set, and stop if apt would remove anything else. **Never run a general `apt autoremove` for this:** on one developer machine it would have removed the CUDA toolkit.
- **Per kernel flavour,** so a distribution-signed fallback kernel kept for Secure Boot is untouched, and each flavour keeps its own two.
- **Each build of our kernel needs its own release name.** A rebuild under the same name replaces the old kernel in place and leaves nothing to fall back to.
- **In the edition** (sparky-stereo-boot 0.1.4): the kernel hook `/etc/kernel/postinst.d/zz-sparky-stereo-kernel-keep` only records the install, because apt and dpkg hold their lock while hooks run; `sparky-stereo-kernel-keep.service` waits until they are done, does the work and logs one line per removed kernel. Nothing happens in a live session, a chroot or a container. `/usr/lib/sparky-stereo-boot/kernel-keep.py --dry-run` prints the plan.

## Boot chain

Daniel, 2026-10-30: "all kernel purges must locate all that kernel parts and regenerate not only grub, but also "update initramfs" with all, same apply to plymouth changes or anything that touches that part".

- **Every boot image, every time.** Debian's `update-initramfs -u`, which every package trigger runs (Plymouth's, the firmware's, the edition's), rebuilds only the newest kernel's boot image while `/etc/initramfs-tools/update-initramfs.conf` says `update_initramfs=yes` (initramfs-tools 0.151, `update-initramfs` lines 400-401). On 2026-10-30 one machine's older kernel had a boot image five days behind its Plymouth and boot changes.
- **The edition sets `update_initramfs=all`,** so the same `-u` rebuilds every installed kernel. sparky-stereo-boot moves initramfs-tools' file aside with `dpkg-divert --rename` to `update-initramfs.conf.debian` and makes its name a link to its own conffile beside it; removal brings Debian's file back. Debian Policy chapter 19 warns against diverting a conffile in place, and dpkg keeps conffiles on removal, so a diversion renamed back over the edition's own conffile would fail: the link avoids both.
- **After a kernel removal,** `update-initramfs -u -k all` and `update-grub` run explicitly.
- **No speed trade-off** (Daniel, the same evening: "the user already chooses when to update, so, why bother so much with speed at this time? ... it's better for us to do all things here - and for themes is the only way to update the boot image").
- **A package that changes the boot image** activates the `update-initramfs` trigger; one that changes what GRUB's menu says (background, theme, translations) runs `update-grub`.
- **Proof:** after a theme change and `update-initramfs -u`, `lsinitramfs` of every kept kernel's boot image lists the theme.

## Logs and crash dumps

- **The journal is the one system log.** No rsyslog copy beside it: that copy was about 480 MB of plain text on one machine. It keeps errors and worse, capped in size and age.
- **logrotate compresses** and caps whatever remains. Logs of non-critical programs are off.
- **Crash dumps stay, capped small.** KDE's crash reporter (DrKonqi) reads them through systemd-coredump. systemd's default cap of 10% of the disk, up to 4 GB, is too much for a desktop.
- **A "detailed logs" switch** for troubleshooting: the user chooses.

## GRUB

- **One system:** hidden menu, with Esc or Shift to open it.
- **Another system found at installation** (especially on UEFI): other systems listed (`GRUB_DISABLE_OS_PROBER=false`) and the menu shown.
- **Proposal:** show the menu after a boot that did not finish, so the kept older kernel is reachable. GRUB cannot write its environment block on Btrfs, LVM, RAID or an encrypted `/boot`; use a short visible timeout there.

## Keeping a user's settings

- **An existing home is not overwritten.** Sparky's installer copied `/etc/skel` over a kept `/home`, so a user who kept their home lost their settings. The one-flag fix (`--ignore-existing` on that copy) and a question (keep the settings, the default, or take the edition's with the old files in a dated backup) are offered to Sparky: [sparky-backup-core #3](https://github.com/sparkylinux/sparky-backup-core/pull/3) and [#4](https://github.com/sparkylinux/sparky-backup-core/pull/4), [calamares-sparky #1](https://github.com/sparkylinux/calamares-sparky/pull/1), in review.
- **KConfig drops comments** when it rewrites a file: an option parked for later goes in a side file, never in a comment.
- **PipeWire skips a whole configuration file on one syntax error** ("Expected object key"); check a file with `pw-config --name pipewire.conf merge context.properties`. Its node names carry the PCI address and break when the bus renumbers: match cards by name and profile, and rename them.

## Cleaning a system safely

1. **Diagnose before deleting.** Group crash dumps by where they ran: containers, the user's session, system services. Read the stack traces of the real desktop crashes. On 2026-10-07 this found the VA-API to VDPAU bridge (`vdpau-va-driver`) segfaulting any VA-API probe on a DRM display; the NVDEC-based `nvidia-vaapi-driver` replaced it. Count journal lines per unit and priority to find what fills the log.
2. **Dry-run every removal** (`apt-get -s`). Read what else it would install, upgrade or remove. A per-version companion package that installed tools still depend on must stay, or apt upgrades those tools behind your back.
3. **Look at each folder before removing it:** owner (`dpkg -S`; on merged-usr, check both `/lib` and `/usr/lib` paths), whether a matching package is installed, what is inside.
4. **Keep what explains a crash** you may report (one dump, its trace) before cleaning the rest.
