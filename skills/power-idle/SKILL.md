---
metadata:
  requires-packages: powerdevil
name: power-idle
description: >-
  KDE power, locking, idle, lid, CEC, swap and hibernate policy in the edition: powerdevilrc and kscreenlockerrc
  defaults, HoldProfile and powerprofilesctl, CEC ownership, text consoles and system power, the Cushion Swap file on
  disk (zram and zswap never ours, the person's opt-in from the Memory page), resume= and RESUME_OFFSET for hibernation,
  a user preference that appears ignored, a failed hibernation read from that attempt (the notice names the device, the share or the cause). Load it when the screen locks or sleeps against the person's setting, the lid
  closes and the TV goes dark, hibernate fails to resume, a zram package removes another package or an upgrade proposes
  removing it, the Memory page needs a swap indicator, or a power profile is held by a program, or Hibernate fails and the Problems page only says the service failed.
---

# Power and idle in KDE

**Check freshness first.**
Written on 2026-10-10.
The general [`sparky-stereo`](../sparky-stereo/SKILL.md) skill comes first.

## Working recipe

1. Read effective user and system settings and identify the daemon that owns the action; distinguish default, absent and explicit values.
2. Reproduce on a private session timeline. Test user overrides and restart/reload separately from the shipped defaults.
3. Return observed action times and the effective settings. Configuration tests do not prove physical suspend, locking or the GL show ran.

Written 2026-10-10 from the accepted power/idle work, swap and hibernate included.
Check the edition's current README and decisions before changing a default.
Load [sparky-stereo](../sparky-stereo/SKILL.md) first, and [edition-packaging](../edition-packaging/SKILL.md) when packaging.

## The owning layer

Ship system defaults in `/etc/xdg/powerdevilrc` and `/etc/xdg/kscreenlockerrc`, with the user's KConfig values taking precedence.
A daemon change is needed only where a setting cannot express the policy.
The accepted desktop/laptop AC distinction uses PowerDevil's own UPower `LidIsPresent` detection.
Kirigami tablet mode does not identify a laptop.
An absent automatic-sleep action can take the hardware default; an explicit user action must remain explicit.
Keep the exported older default API's semantics and preserve migrated choices.
Capability suppression in a VM is separate from hardware defaults; test both, or a VM can hide the wrong value.

The accepted timeline, in seconds, is:

| Mode | Dim | Screen off and lock | Automatic sleep |
| --- | ---: | ---: | ---: |
| Desktop AC | 900 | 9900 | Never |
| Laptop AC | 900 | 9900 | 14400 |
| Battery | 900 | 1200 | 1800 |
| LowBattery | 180 | 300 | 600 |

The desktop/AC GL-show boundary is 8100 seconds.
The show itself is a separate component; configuration and screen-off proof do not prove it ran.
Independent idle locking is disabled; lock-before-off and lock-on-resume remain enabled.
Dimming remains gated by brightness hardware.
The power button uses native Shutdown everywhere; native session management asks programs to save.
Battery lid closure sleeps.
The AC lid keeps the internal output enabled and its layout unchanged while its panel is off.
This belongs in KWin's output configuration and DPMS handling.
Also test new windows, transient placement, pointer movement and opening the lid during global DPMS Off.

## Prove settings and behavior separately

Compile the real generated PowerDevil and screen-locker settings classes against the shipped conffiles.
Include desktops, laptops without a battery, UPS desktops, peripheral batteries, tablet mode, VM/capability suppression and user overrides.
Run the migration helper too: explicit old Sleep choices must survive a new desktop NoAction default.

For runtime, observe native KScreen DPMS and the native locker from the packaged daemon in a private headless KWin session.
A calibrated accelerated clock can shorten the idle wait; keep the observer clock unaccelerated.
Record every boundary against its expected time.
Removing lock-before-off must fail the lock check even when DPMS still turns off.
Mock logind requests do not prove a physical suspend or resume.

KWin's own lid/output tests and native CI are separate from that daemon runtime fixture.
Compare failing CI cases with the same unmodified release.
Keep headless fixture repairs separate from production patches for rebasing.

## CEC ownership

Screen-off may turn the TV off only while it shows this PC.
Broadcast Request Active Source (0x85), then accept an Active Source (0x82) reply only with this adapter's physical address.
No reply or another address means no Standby, with a reason logged.
Remember only an acknowledged Standby sent by this controller.
Wake then sends Image View On (0x04), followed by Active Source with that same physical address.
Initial wake and a TV this controller did not put to sleep must not take another input away.

Assert the exact traffic for another source, no reply and our source.
Remove the ownership check once: the other-source test must fail.
A native controller and real cec-ctl over an ioctl fixture prove the protocol decisions, not a physical TV or the kernel vivid cycle.
Without an adapter, leave DPMS alone.

## Text consoles and system power

Session defaults and headless tests do not prove tty1/tty2 isolation.
Use an isolated development VM, with Plasma on a different VT, and measure both text consoles before and across the shortened timeline, including each console in foreground.
Read the kernel consoleblank value, KD_TEXT mode, blanked-VT query, console buffer and available framebuffer/DPMS power state.
Watch for blanking programs and ioctl/writer activity.
Plant a real tty2 blank and require the same detector to fail.
Missing guest prerequisites are not a pass.
The kernel's blanked-VT query is global, not per-output DPMS.

Preparing the probe or passing its logic tests does not establish the VM result; run it in the VM and keep its JSON.
Keep guest credentials with their owner.
Three things only the real guest showed: a Wayland client allocates its object ids from 3 with no gaps (libwayland's rule; KWin drops a client that skips one), PowerDevil's `reparseConfiguration` reloads only the global settings (call `refreshStatus`, as the KCM does, to apply short timeouts), and DRM's fbdev emulation reads `fb0/blank` as 4 while tty1 is visible, so judge the text display by the DRM connector's DPMS state.

A KIdleTime built against an older Qt minor release can get no Wayland interface from a newer one (Qt 6.11 raised `QWaylandApplication` to revision 2): then no idle action fires at all, no dim, no screen off, no lock.
Check the installed libkf6idletime6 was rebuilt against the running Qt before reading a missing dim as a settings problem.

For game performance use PPD's `HoldProfile` through `powerprofilesctl launch`, so the daemon owns restoration, concurrent holds and disconnect cleanup.
Test the child's actual profile, argument boundaries, failure status, signals and power-saver hold precedence; an argv-only stub is insufficient.
## Memory and swap

The edition keeps pages in RAM (swappiness 1) and swaps to the Cushion Swap File on disk. zram and zswap are never set up by the edition and never on by default, on any machine: nothing for them is installed or configured, and there is no rule that turns them on by hardware. A person who wants zram opts in from Stereo APTus (or the Memory page's shortcut to the same action), which installs Debian's systemd-zram-generator; no edition package Conflicts with or Breaks a zram package, so that choice stays theirs. The publication and image gate (iso-build/zram-check.py in the build repository) refuses any package or image of ours that sets zram or zswap up.
The user can switch it in System Settings, Memory.

The swap is the Cushion Swap File, Daniel Ramos's design: the area stays off at rest, is switched on when available memory runs low or falls fast, and is switched off again only when the arithmetic shows that cannot itself run out of memory.
It wakes through PSI where the kernel has it and polls otherwise.
Measure before trusting PSI alone: with swap off it fires only at the very end, sometimes after the OOM kill, so keep a timed check beside it.

Hibernate with the area off needs two things. logind offers it only with an active swap that can hold the image (systemd's `hibernate-util.c`); the documented `SYSTEMD_BYPASS_HIBERNATION_MEMORY_CHECK=1` for systemd-logind, set by a generator only where an area and `resume=` exist, offers it.
And systemd-sleep looks for the device before its hooks run, so a unit ordered before `systemd-hibernate.service` switches the area on.
A virtio-fs share blocks hibernation in a VM; test without it. zram cannot hold the resume image.

Find where the image goes the way the installer recorded it: `/etc/initramfs-tools/conf.d/resume` (`RESUME=`, `RESUME_OFFSET=` for a swap file, `none` for no hibernation).
Debian resumes from it with no `resume=` on the kernel command line, so a check of `/proc/cmdline` alone misses every installed system. initramfs-tools 0.151 has no `RESUME_OFFSET`, though: its init takes `resume_offset` only from the command line or a conf.d snippet in the image, so a hook must write that snippet.
Measure the kernel's offset after boot; without the hook it is 0.
A swap partition the installer made can sit in no fstab line and must still work.

While a hibernation uses the area, nothing may switch it off: hold retraction from the unit's switch-on until the sleep hook runs, with a timeout for a hibernation that never started.
A systemd generator's stderr reaches neither dmesg nor the journal (systemd.generator(7)), so write its decisions to `/dev/kmsg`.
PowerDevil can keep an old CanHibernate answer while logind's has changed; ask logind when you prove an offer.
Pacing by headroom samples fastest on small machines, and so logs the most there: measure the log volume on the smallest machine you support, not only on yours.

/tmp lives on disk (`tmp.mount` masked, as Debian's trixie release notes describe) and is emptied at every boot.
Keep sysctl and tmpfiles files in their owning package.
A generator fixture does not prove a live swap device.
Read [system-housekeeping](../system-housekeeping/SKILL.md) for system policy.

## Testing hibernate in a VM (2026-11-07)

Use a disposable overlay of the development image, a real swap area named in `conf.d/resume`, a serial console and QEMU `-no-reboot` with a QMP event log; hibernate at least ten times per kernel and repeat with Debian's stock kernel to tell the kernel from QEMU, OVMF and the guest set-up.
A "resume" counts only when the boot id is unchanged and a witness process survived; the journal of the resumed machine looks like an in-place return (`Waking up from system sleep state S4`, `hibernation exit`, no image-writing lines) because the writing lines exist only on the console of the machine that went down.
The recipe, the edition's own path (partition, swap file with `RESUME_OFFSET`, PowerDevil, suspend-then-hibernate), the Secure Boot bench run and the traps are in [references/hibernate-in-a-vm.md](references/hibernate-in-a-vm.md).

## A failed hibernation says why (2026-11-09)

The engine reads a failed `systemd-hibernate`, `systemd-suspend-then-hibernate` or `systemd-hybrid-sleep` from that attempt's journal (systemd-sleep's `SLEEP_STOP` line with `ERRNO=`, the kernel's `PM: failed to freeze async: error -95` with its `_KERNEL_DEVICE`) and names the device and what to do; a virtio-fs share, a locked-down kernel and a missing swap area get no retry, because the cause stays.
The kinds with their source lines, the fixture method (`systemd-journal-remote`), the real virtio-fs run and the traps are in [references/failed-hibernation.md](references/failed-hibernation.md); how any package says a cause instead of "Repair starts it again" is in [system-housekeeping](../system-housekeeping/references/problems-cause-not-retry.md).

## When a user preference appears ignored (2026-10-19)

Record which machine, session and power state were involved, then read the effective user/system values.
Separate automatic idle locking, lock-before-screen-off, lock-on-resume and the GL-show launch path; “Never” in one control must not be assumed to disable every other mechanism.
Trace the action's actual initiator and configuration reload before changing defaults.
Prove explicit user overrides survive restart and migration; keep a timed runtime witness for each suspected action.
A corrected setting without reproduction of the overnight event is a configuration fix, not proof that the underlying runtime defect is fixed.

## Lessons from the lanes, October to November 2026

From the lanes of 25 October to 6 November 2026; add the next lesson here as you work ([ai-partners, skills as you go](../ai-partners/SKILL.md#skills-as-you-go)).

- Memory page opt-in for zram: the Memory package Depends on Cushion Swap (not Recommends) so an install with `--no-install-recommends` still gets the service; verify with a red/green pair (0.1.7 lacks Cushion in Depends, exit 1; 0.1.8 requires it, exit 0) and an isolated apt solve without Recommends. Cushion zram accounting: 0.3.3 wrongly needed 29 GiB instead of 21 GiB for the same disk swap; 0.3.4 passes the 58-case suite. (lane zram-on-at-opt-in-360b)
- Symptom: installing a zram package removes `kernel-settings` or a plain upgrade proposes `Remv systemd-zram-generator` with apt exit 0. Cause: package relations (Conflicts) and an auto-installed generator that apt considers unneeded; a dpkg-installed generator does not mean the person selected it. Fix: no Conflicts or Breaks against any zram package; installing through Stereo APTus marks the generator manual, which releases the guard and keeps it across autoremove; a leftover generator with an empty zram node (disksize 0) is not active swap. Proven with real zram activation only inside a nested QEMU guest (`-cpu max` for TCG). The skill covers the opt-in and "no Conflicts"; add the manual-mark and inherited-generator facts. (lane no-zram-kcm-360)
