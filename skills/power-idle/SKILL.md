---
name: power-idle
description: >-
  Power profiles, idle timelines, locking, laptop lids, HDMI-CEC, zram by
  hardware, the Cushion Swap File and hibernate in Sparky
  Stereo OS's KDE session, with native Plasma settings tests and text-console
  isolation proof. Load sparky-stereo first; use edition-packaging for packages.
---

# Power and idle in KDE

Written 2026-10-10 from the accepted power/idle work, swap and hibernate included. Check the edition's
current README and decisions before changing a default. Load
[sparky-stereo](../sparky-stereo/SKILL.md) first, and
[edition-packaging](../edition-packaging/SKILL.md) when packaging.

## The owning layer

Ship system defaults in `/etc/xdg/powerdevilrc` and
`/etc/xdg/kscreenlockerrc`, with the user's KConfig values taking precedence.
A daemon change is needed only where a setting cannot express the policy.
The accepted desktop/laptop AC distinction uses PowerDevil's own UPower
`LidIsPresent` detection. Kirigami tablet mode does not identify a laptop.
An absent automatic-sleep action can take the hardware default; an explicit
user action must remain explicit. Keep the exported older default API's
semantics and preserve migrated choices. Capability suppression in a VM is
separate from hardware defaults; test both, or a VM can hide the wrong value.

The accepted timeline, in seconds, is:

| Mode | Dim | Screen off and lock | Automatic sleep |
| --- | ---: | ---: | ---: |
| Desktop AC | 900 | 9900 | Never |
| Laptop AC | 900 | 9900 | 14400 |
| Battery | 900 | 1200 | 1800 |
| LowBattery | 180 | 300 | 600 |

The desktop/AC GL-show boundary is 8100 seconds. The show itself is a
separate component; configuration and screen-off proof do not prove it ran.
Independent idle locking is disabled; lock-before-off and lock-on-resume
remain enabled. Dimming remains gated by brightness hardware. The power button uses native
Shutdown everywhere; native session management asks programs to save.
Battery lid closure sleeps. The AC lid keeps the internal output enabled
and its layout unchanged while its panel is off. This belongs in KWin's
output configuration and DPMS handling. Also test new windows, transient
placement, pointer movement and opening the lid during global DPMS Off.

## Prove settings and behavior separately

Compile the real generated PowerDevil and screen-locker settings classes
against the shipped conffiles. Include desktops, laptops without a battery,
UPS desktops, peripheral batteries, tablet mode, VM/capability suppression
and user overrides. Run the migration helper too: explicit old Sleep choices
must survive a new desktop NoAction default.

For runtime, observe native KScreen DPMS and the native locker from the
packaged daemon in a private headless KWin session. A calibrated accelerated
clock can shorten the idle wait; keep the observer clock unaccelerated.
Record every boundary against its expected time. Removing lock-before-off
must fail the lock check even when DPMS still turns off. Mock logind requests
do not prove a physical suspend or resume.

KWin's own lid/output tests and native CI are separate from that daemon
runtime fixture. Compare failing CI cases with the same unmodified release.
Keep headless fixture repairs separate from production patches for rebasing.

## CEC ownership

Screen-off may turn the TV off only while it shows this PC. Broadcast
Request Active Source (0x85), then accept an Active Source (0x82) reply only
with this adapter's physical address. No reply or another address means no
Standby, with a reason logged. Remember only an acknowledged Standby sent
by this controller. Wake then sends Image View On (0x04), followed by Active
Source with that same physical address. Initial wake and a TV this controller
did not put to sleep must not take another input away.

Assert the exact traffic for another source, no reply and our source. Remove
the ownership check once: the other-source test must fail. A native controller
and real cec-ctl over an ioctl fixture prove the protocol decisions, not a
physical TV or the kernel vivid cycle. Without an adapter, leave DPMS alone.

## Text consoles and system power

Session defaults and headless tests do not prove tty1/tty2 isolation. Use an
isolated development VM, with Plasma on a different VT, and measure both text
consoles before and across the shortened timeline, including each console
in foreground. Read the kernel consoleblank value, KD_TEXT mode, blanked-VT
query, console buffer and available framebuffer/DPMS power state. Watch for
blanking programs and ioctl/writer activity. Plant a real tty2 blank and
require the same detector to fail. Missing guest prerequisites are not a
pass. The kernel's blanked-VT query is global, not per-output DPMS.

Preparing the probe or passing its logic tests does not establish the VM
result; run it in the VM and keep its JSON. Keep guest credentials with their
owner. Three things only the real guest showed: a Wayland client allocates
its object ids from 3 with no gaps (libwayland's rule; KWin drops a client
that skips one), PowerDevil's `reparseConfiguration` reloads only the global
settings (call `refreshStatus`, as the KCM does, to apply short timeouts), and
DRM's fbdev emulation reads `fb0/blank` as 4 while tty1 is visible, so judge
the text display by the DRM connector's DPMS state.

A KIdleTime built against an older Qt minor release can get no Wayland
interface from a newer one (Qt 6.11 raised `QWaylandApplication` to revision
2): then no idle action fires at all, no dim, no screen off, no lock. Check
the installed libkf6idletime6 was rebuilt against the running Qt before
reading a missing dim as a settings problem.

For game performance use PPD's `HoldProfile` through `powerprofilesctl launch`,
so the daemon owns restoration, concurrent holds and disconnect cleanup.
Test the child's actual profile, argument boundaries, failure status,
signals and power-saver hold precedence; an argv-only stub is insufficient.
## Memory and swap

The edition keeps pages in RAM (swappiness 1, with or without zram). zram is
decided by hardware: zram-generator's own `set!` directive runs a script
that answers 1 or 0 and multiplies the device size, so a capable machine gets
no zram unit at all; it is on with 8 GB of RAM or less, or when the swap area
sits on eMMC, an SD card, a rotating disk or removable storage. lz4, because
the machines that get zram have the least CPU to spare. The user can switch
it in System Settings, Memory.

The swap is the Cushion Swap File, Daniel Ramos's design: the area stays off
at rest, is switched on when available memory runs low or falls fast, and is
switched off again only when the arithmetic shows that cannot itself run out
of memory. It wakes through PSI where the kernel has it and polls otherwise.
Measure before trusting PSI alone: with swap off it fires only at the very
end, sometimes after the OOM kill, so keep a timed check beside it.

Hibernate with the area off needs two things. logind offers it only with an
active swap that can hold the image (systemd's `hibernate-util.c`); the
documented `SYSTEMD_BYPASS_HIBERNATION_MEMORY_CHECK=1` for systemd-logind,
set by a generator only where an area and `resume=` exist, offers it. And
systemd-sleep looks for the device before its hooks run, so a unit ordered
before `systemd-hibernate.service` switches the area on. A virtio-fs share
blocks hibernation in a VM; test without it. zram cannot hold the resume
image.

Find where the image goes the way the installer recorded it:
`/etc/initramfs-tools/conf.d/resume` (`RESUME=`, `RESUME_OFFSET=` for a swap
file, `none` for no hibernation). Debian resumes from it with no `resume=` on
the kernel command line, so a check of `/proc/cmdline` alone misses every
installed system. initramfs-tools 0.151 has no `RESUME_OFFSET`, though: its
init takes `resume_offset` only from the command line or a conf.d snippet in
the image, so a hook must write that snippet. Measure the kernel's offset after
boot; without the hook it is 0. A swap partition the installer made can sit in
no fstab line and must still work.

While a hibernation uses the area, nothing may switch it off: hold retraction
from the unit's switch-on until the sleep hook runs, with a timeout for a
hibernation that never started. A systemd generator's stderr reaches neither
dmesg nor the journal (systemd.generator(7)), so write its decisions to
`/dev/kmsg`. PowerDevil can keep an old CanHibernate answer while logind's has
changed; ask logind when you prove an offer. Pacing by headroom samples
fastest on small machines, and so logs the most there: measure the log volume
on the smallest machine you support, not only on yours.

/tmp lives on disk (`tmp.mount` masked, as Debian's trixie release notes
describe) and is emptied at every boot. Keep zram, sysctl and tmpfiles files
in their owning package. A generator fixture does not prove a live swap
device. Read [system-housekeeping](../system-housekeeping/SKILL.md) for
system policy.
