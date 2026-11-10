---
metadata:
  requires-packages: systemd
name: system-housekeeping
description: >-
  Bounded logs, kernel retention and cleanup that keep user settings, boot recovery and diagnostic evidence:
  old kernels per flavour (APT::NeverAutoRemove::KernelCount, never a general apt autoremove), update-initramfs for
  every image, GRUB and grub-editenv or update-grub tested in a container, the journal as the one log, crash dumps
  capped, /etc/skel and existing homes, local system mail in /var/mail, BleachBit, which scratch folders are safe to
  delete, services that fail on hardware the machine lacks, PipeWire's one-error configuration files, KConfig dropping
  comments. Load it when a disk fills with kernels or logs, a removal would take the running kernel, a cleaner would
  delete the evidence of a crash or shows Access denied on a mailbox, a tool exits 0 with no message on an unreadable
  HOME, system mail piles up, nvidia-persistenced fails on a machine without the card, thermald fails at every boot on an
  AMD CPU, or a GRUB test in a container shows English and an empty menu.
---

# System housekeeping

## Working recipe

1. Identify package ownership, running and fallback kernels, disk consumers and the diagnostic material needed before removal.
2. Simulate the specific package transaction, inspect dependencies and preserve one useful crash trace; use an isolated fixture for automatic policy.
3. Return the reviewed removal set and recovery evidence. Never substitute broad autoremove for the kernel-only policy.

**Check freshness first.**
Written on 2026-10-07; old kernels and the boot chain revised on 2026-10-30; local system mail added on 2026-11-06.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

Daniel's rule: "we don't grow so fast, and when grow self prune".
A user's disk must not creep up because Linux keeps everything.

## /tmp on disk, and kept

Daniel's design: /tmp is a plain folder on the disk (tmp.mount masked), and it keeps its files: no wipe at boot and no age cleanup. "make sure the tmp cleaner is really off - we do not want to keep the ram tmp behaviour, and was one of the reasons to move it to the disk" (2026-11-06).

- **Debian's own rule still cleans.** `/usr/lib/tmpfiles.d/tmp.conf` says `q /tmp 1777 root root 10d`: no boot wipe (`q`, not `D`), but the daily `systemd-tmpfiles-clean` timer deletes what is untouched for 10 days. Moving /tmp to the disk does not remove that.
- **The fix is a conffile of the same name in /etc.** `sparky-stereo-kernel-settings` ships `/etc/tmpfiles.d/tmp.conf` with `q /tmp 1777 root root -` and Debian's `q /var/tmp 1777 root root 30d`. A file in `/etc/tmpfiles.d` masks the one of the same name in `/usr/lib/tmpfiles.d` (tmpfiles.d(5)); an age of `-` means no cleanup. Debian's file holds only those two rules, so nothing else is lost.
- **A conffile, not a /usr/lib file:** a person who wants an age edits it and dpkg keeps the edit on upgrade.
- **Never ship a wipe or an age of ours.** The edition once shipped `D /tmp ... 10d` (boot wipe) under Daniel's name; he never asked for it.

### Testing it (container, root)

1. `systemd-tmpfiles --cat-config`: the `/tmp` line must be `q /tmp 1777 root root -`, and the 10d line must be gone.
2. Build a fixture root (`--root=DIR` with `usr/lib/tmpfiles.d/tmp.conf` copied from Debian, plus the package's `etc/tmpfiles.d/tmp.conf`), put a file in `DIR/tmp` and `DIR/var/tmp`, and run `datefudge '11 days' systemd-tmpfiles --root=DIR --clean`. Debian's file alone removes the /tmp file (the red control); the package keeps it. `datefudge '31 days'` still removes from /var/tmp.
3. `--clean --dry-run` prints "Would remove" only at `SYSTEMD_LOG_LEVEL=debug`; at the default level it shows nothing and proves nothing, so run a control that must list a file.
4. Upgrade: install the published package, then the new one with plain `dpkg -i` and stdin from /dev/null. An existing identical file is adopted without a prompt; a person's edit is kept.

### Traps

- **libfaketime cannot age files:** it shifts the `stat()` times too, so a file always looks as old as it was created and `--clean` removes nothing. Use `datefudge`, which moves only the clock. A file's change and birth times cannot be set back with `touch`, and systemd ages by all of them, so the clock has to move.
- **Lean Code strips comments from a shipped conffile** (the explanation, with Daniel's quote, lives in the authored source and the `-lc-hr` companion). A hand-made file with comments on a machine then differs from the package's file: dpkg asks, and either answer gives the same rules.
- **A conffile that `--root` fixtures need is found by name:** copy Debian's file into the fixture root first, or the control proves nothing.

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
- **An error on the image or the menu:** [every message the edition's configuration can make GRUB print](references/grub-errors.md), booted in QEMU, with the recipe that reads them from the serial port.
- **Proposal:** show the menu after a boot that did not finish, so the kept older kernel is reachable. GRUB cannot write its environment block on Btrfs, LVM, RAID or an encrypted `/boot`; use a short visible timeout there.

## Keeping a user's settings

- **An existing home is not overwritten.** Sparky's installer copied `/etc/skel` over a kept `/home`, so a user who kept their home lost their settings. The one-flag fix (`--ignore-existing` on that copy) and a question (keep the settings, the default, or take the edition's with the old files in a dated backup) are offered to Sparky: [sparky-backup-core #3](https://github.com/sparkylinux/sparky-backup-core/pull/3) and [#4](https://github.com/sparkylinux/sparky-backup-core/pull/4), [calamares-sparky #1](https://github.com/sparkylinux/calamares-sparky/pull/1), in review.
- **KConfig drops comments** when it rewrites a file: an option parked for later goes in a side file, never in a comment.
- **PipeWire skips a whole configuration file on one syntax error** ("Expected object key"); check a file with `pw-config --name pipewire.conf merge context.properties`. Its node names carry the PCI address and break when the bus renumbers: match cards by name and profile, and rename them.

## Local system mail

A Debian system mails itself: cron, anacron and sudo notices, netdata and security-check alerts (chkrootkit, rkhunter), the bounce of a message nobody could deliver.
Daniel, 2026-11-05: "that cleaning was due long ago".

- **Where it piles up.** `/var/mail/USER`, one mailbox per account. Debian Policy 11.6: the mail spool is `/var/mail`, `2775 root:mail`, and a mailbox is `600` owned by the user or `660` owned by `user:mail`. A person can therefore empty their mailbox but cannot delete it, and root can do both. `~/dead.letter` and `/root/dead.letter` keep a copy of a message a mail program could not send (a failed security alert is the usual one). `/root/mbox` holds mail root has read. The queue folders of a mail program (`/var/spool/exim4`, `/var/spool/postfix/{active,bounce,corrupt,defer,deferred,flush,hold,incoming,maildrop,saved,trace}`, `/var/spool/nullmailer/{queue,failed,tmp}`, `/var/spool/dma`, a person's `~/.msmtp.queue`) outlive the program when it is removed without a purge. Postfix's other folders under `/var/spool/postfix` are its chroot (libraries, `resolv.conf`), not mail.
- **What is system mail.** Mail a machine wrote to itself. Look at the senders and subjects before you call a mailbox "his data": count them (`grep -c '^From '`, `grep '^Subject:' | sort | uniq -c | sort -rn`). A person's own mail is not system mail, and the local mailbox can hold some: the cleaner says so in its warning.
- **How the cleaner treats it.** `sparky-stereo-housekeeping` adds BleachBit's cleaner `system_mail`, never ticked: `mailbox` (the running account's mailbox, emptied in place, so owner and mode stay), `mailboxes` (every mailbox and `/root/mbox`, administrator), `dead_letter`, and `queues`. A queue is offered only when dpkg says every package of its mail program is gone (`dpkg-query -W -f='${db:Status-Status}'` is `not-installed` or `config-files`) and the program is not on the system; CleanerML has no such condition, so dpkg's trigger writes the offer again whenever a mail program is installed or removed. The queue of an installed mail program is never touched. Preview first (`bleachbit --preview system_mail.mailbox`); a file it cannot clear is named in the output (`Access denied: ...`).
- **After clearing,** check that the spool still works: `/var/mail` `2775 root:mail`, the mailbox `user:mail 0660`, `/var/spool/dma` `2775 root:mail` (dma's Makefile). On the station `/var/spool/dma` had been `root:root 755` since 2020, so chkrootkit's mail failed every night until it was put right.
- **BleachBit does not take the mailbox lock** that Policy 11.6 asks every mail program to take (`fcntl()` plus dot locking). Empty a mailbox when nothing is delivering to it.
- **Translations.** BleachBit translates a cleaner's text with its own gettext domain `bleachbit`, which Debian's package owns. The package diverts the catalogs of the required languages (`de es fr ja ko pl pt_BR zh_CN zh_TW`; `es` since ORDER 507), writes Debian's with its strings added, and gives Debian's back when it is removed. A translation test needs a real locale (`localedef`), because gettext translates nothing in `C`.

## Services that only one vendor's hardware can run

Symptom: `systemctl --failed` lists a unit at every boot on one kind of machine and not on another (thermald on an AMD CPU: it prints "Unsupported cpu model or platform", leaves without taking its D-Bus name and its `Type=dbus` unit fails; nvidia-persistenced on a machine without the card; NVIDIA's IMEX daemon, which needs a multi-node NVLink domain).
Debian's postinst enables such a unit wherever the package is installed, so the fix is to decide **who gets the package**, not to mask the unit.

1. **Find them.** Simulate the image's closure (`apt-get -s install sparky-stereo | grep '^Inst'`) and look for services that name one vendor, one card or one fabric. Then run the daemon's own command line once on each side in a container and read its message. A container can show a CPU vendor: `-v FIXTURE:/proc/cpuinfo:ro` bind-mounts over the file, but a daemon that reads CPUID (thermald does) still sees the host's CPU, so the fixture proves the detection and the gate, not the daemon.
2. **Decide in the detection, never in a list.** The hardware tool picks packages from the captured facts (`vendor_id` in `/proc/cpuinfo`, `lspci`): `GenuineIntel` adds thermald, laptop or desktop; a metapackage's list never names it, because a Depends installs it everywhere. A machine that already has the package keeps it (an upgrade removes nothing), so a package list change alone leaves AMD machines that got thermald from an earlier image still failing.
3. **A service the person installed by hand is theirs.** Do not gate, mask or drop-in a vendor-specific unit to hide its failure: Daniel, 2026-11-07, "If manually installed leave it, maybe a intel user is planning a migration". A thermald or nvidia-imex marked manual stays exactly as the person made it, even where its unit fails. An earlier version of this lane shipped `ExecCondition=` and `Condition...=` drop-ins for them; they were removed for this reason. If a package of the edition never installs a service (nvidia-imex, urfkill), any copy is the person's and needs nothing from us.
4. **Machines that got the package from an earlier image are settled once, after the apt run.** The old metapackage installed thermald as an automatic package everywhere, and the new one no longer depends on it. A script run by the postinst and by dpkg's post-invoke hook starts a oneshot unit with `systemctl --no-block` (inside an apt run apt rewrites its state file at the end, so a change made earlier is lost); the unit waits with `apt-get -o DPkg::Lock::Timeout=-1 check`, then: on the vendor, marks the package manual (so `apt autoremove` keeps it); on any other vendor, removes it with `apt-get remove` (configuration kept) only when it is automatic and `apt-get -s remove` lists nothing but it; a manual one is left. A stamp makes it run once, and the journal gets one line saying why. A package that something still depends on is left, with no stamp, and looked at again at the next dpkg run.
5. **Prove it with fixtures on both sides.** Detection: one fixture folder per case (Intel and AMD, laptop and desktop) through `sparky-stereo-hardware --auto --dry-run --fixture DIR`, red on the published package and green on the new one. The settling step: four containers (Intel and AMD, installed automatic and manual) with a cpuinfo fixture bind-mounted over `/proc/cpuinfo`, running the unit's own command (a container has no systemd): Intel automatic gives manual and `apt-get -s autoremove` stops listing it, AMD automatic gives removed with the configuration kept and a second run does nothing, both manual cases are untouched, and a package that depends on it keeps it. Upgrade: published packages first, then the new ones, judged on apt's `Inst` and `Remv` lines (none), then the diff of `dpkg-query` before and after the step (exactly the one package).

## Cleaning a system safely

1. **Diagnose before deleting.** Group crash dumps by where they ran: containers, the user's session, system services. Read the stack traces of the real desktop crashes. On 2026-10-07 this found the VA-API to VDPAU bridge (`vdpau-va-driver`) segfaulting any VA-API probe on a DRM display; the NVDEC-based `nvidia-vaapi-driver` replaced it. Count journal lines per unit and priority to find what fills the log.
2. **Dry-run every removal** (`apt-get -s`). Read what else it would install, upgrade or remove. A per-version companion package that installed tools still depend on must stay, or apt upgrades those tools behind your back.
3. **Look at each folder before removing it:** owner (`dpkg -S`; on merged-usr, check both `/lib` and `/usr/lib` paths), whether a matching package is installed, what is inside.
4. **Keep what explains a crash** you may report (one dump, its trace) before cleaning the rest.

## Kept problems: dismiss and bring back

The engine that keeps what failed lets the person dismiss a problem, and the Problems page of System Settings lists the current and the dismissed ones.
[Dismiss, Bring back and the page](references/problems-dismiss.md) says what each scope does (a failed service of this boot stays dismissed when it fails the same way after a reboot), the one store the notifier and the page share, and the traps met.
[A problem that says its cause](references/problems-cause-not-retry.md) is the recipe for a failure whose cause stays: its own message, no blind "Repair starts it again", an `ExecStopPost=` for a unit that ends well, and fixtures from real journals.

## Lessons from the lanes, October to November 2026

[Lessons from the lanes](references/lessons-2026-11.md) keeps what the lanes of 25 October to 6 November 2026 learned on this part: the recipes that worked, each trap with its symptom, its cause, its fix and how the cause was found, the perks and the measured facts (10 entries).
Read the traps before a change to this part, and add the next lesson there as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).
