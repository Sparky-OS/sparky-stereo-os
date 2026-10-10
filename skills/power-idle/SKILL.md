---
name: power-idle
description: >-
  Power profiles, idle timelines, locking, laptop lids and HDMI-CEC in Sparky
  Stereo OS's KDE session, with native Plasma settings tests and text-console
  isolation proof. Load sparky-stereo first; use edition-packaging for packages.
---

# Power and idle in KDE

Written 2026-10-10 from the accepted power/idle work. Check the edition's
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

The person who owns the VM runs this probe and retains its JSON. Preparing
it or passing its logic tests does not establish the VM result. Keep guest
credentials with their owner.

For game performance use PPD's `HoldProfile` through `powerprofilesctl launch`,
so the daemon owns restoration, concurrent holds and disconnect cleanup.
Test the child's actual profile, argument boundaries, failure status,
signals and power-saver hold precedence; an argv-only stub is insufficient.
Keep zram/sysctl files in their existing owning package. Test native generator
sizing at either side of the cap and administrator overrides. A generator
fixture does not prove a live swap device. Retain disk swap for hibernation:
zram cannot hold the resume image. Read
[system-housekeeping](../system-housekeeping/SKILL.md) for system policy.
