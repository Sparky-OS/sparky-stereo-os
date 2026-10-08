---
name: system-housekeeping
description: >-
  The edition's self-pruning defaults (old kernels removed when a new one installs, minimal capped logs, crash dumps kept small, GRUB menu rules) and how to diagnose and clean a system safely: dry runs, kernel-only removals, reading crash dumps before deleting them. Load the general sparky-stereo skill first.
---

# System housekeeping

**Check freshness first.** Written on 2026-10-07. The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

Daniel's rule: "we don't grow so fast, and when grow self prune". A user's disk must not creep up because Linux keeps everything.

## Old kernels

- **When:** right after a new kernel has installed successfully, meaning its boot image and GRUB entry were written. A failed install never removes anything.
- **What stays:** the running kernel and the newest. If the newest is the running one, the one before it. That is apt's own rule (`APT::NeverAutoRemove::KernelCount`, default 2).
- **What goes:** kernel packages only (image, headers, modules, kbuild, the per-version base package), purged, together with their orphaned `/lib/modules/<version>` folders and DKMS records. **Never run a general `apt autoremove` for this:** on one developer machine it would have removed the CUDA toolkit.
- **Per kernel flavour,** so a distribution-signed fallback kernel kept for Secure Boot is untouched.
- **Each build of our kernel needs its own release name.** A rebuild under the same name replaces the old kernel in place and leaves nothing to fall back to.

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
