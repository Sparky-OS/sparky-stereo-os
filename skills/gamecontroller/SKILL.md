---
name: gamecontroller
description: >-
  Extend or verify KDE's Game Controller page for flight and racing rigs,
  preserving every raw SDL control and checking controller database labels.
  Load sparky-stereo first; use edition-packaging for a data package.
---

# KDE controller input

Written on 2026-10-10. Load [sparky-stereo](../sparky-stereo/SKILL.md) first.
Follow [house formats](../../docs/house-formats.md): every button, axis and hat
stays raw inside the system. The game or the user's mapping owns conversion.
Hardware counts determine the model; gamepad names describe a presentation.

## Preserve the raw device

The accepted raw-controls base is plasma-desktop v6.7.4 with commit
`30a4e86b23` on `sparky/gamecontroller-raw-controls` in
[the edition's Plasma fork](https://invent.kde.org/danielcamposramos/plasma-desktop).
Check the current integration branch before carrying changes to another release.

Keep raw axes indexed by SDL axis number. SDL gamepad axes are separate enums;
they must not replace the raw axis list. Keep hats indexed and labelled, with
both components represented. Unknown controls retain their numbered identity.
KDE cannot recover controls already lost in the kernel, SDL or Wine.

Use an SDL virtual joystick for the page and model tests. A useful fixture has
128 buttons, 12 axes and 8 hats, distinct values on each axis and hat, and the
last button held. Check counts, values, labels and the final rendered delegates.
Include a planted dropped-control error and require the validator to reject it.
Run the full page with software rendering, offscreen Qt or container-local Xvfb.
Inspect its QML log and screenshots. Keep long labels bounded and their full
text available in a plain-text tooltip; verify hover explicitly in offscreen
Qt, where it can default to disabled.

## Accepted database consumer

The database consumer on `66f11d4886` was accepted on 2026-10-10. Its follow-up
`aca514709d` reads profiles directly, so local edits appear on the page.

Keep upstream data in a separately synced package, with repository, exact
revision, file hashes and upstream licence notices. Missing or invalid data
must fall back to numbered controls. Contribute missing rig records upstream;
do not edit a private copy of the database.

RetroArch profiles require an exact nonzero VID/PID, name and input driver.
Its udev indices are evdev indices, so they provide identity only to an SDL
consumer. Its mapped SDL2 driver uses gamepad enums, so those profiles also
provide identity only. Only unmapped SDL2 profiles can label raw SDL indices.
Match mapped profile names through SDL's game-controller name.

Let SDL's official mapping loader select platform and GUID mappings. Attribute
an installed mapping only when its canonical fingerprint matches what SDL
actually selected. Retain conflicting upstream labels and their source rather
than guessing a preferred name. Test malformed profiles, duplicate fields,
path traversal, local edits, unlisted profiles, driver mismatches and sparse mappings.
The page reads manifests only for repository and revision provenance. It does
not verify file hashes or use the manifest as an allowlist. Hash verification
belongs in the package builder and its integrity checks.

## Build evidence

Use the edition's kde-ci-local tool and its shared cache and build lock. Keep
both lint and build results tied to one exact source commit. Freeze the invoked
shell wrapper for each run; edit the recorded recipe for later invocations. Compare all six
jobs with an unpatched release baseline using the same SDK and CI utilities
per job. Record each container's actual utility revisions: the runner's pinned
templates alone do not pin the scripts cloned inside a job.

Compile focused Qt tests with KDE's `QT_USE_QSTRINGBUILDER` flag. Use explicit
byte-array containers for their expected data so conversion assumptions do
not hide a CI compile failure.

The v6.7.4 container baseline has twelve at-spi startup failures because it lacks
a systemd user instance. Exclude them only after checking the same names,
statuses and causes in the matching unpatched job. Any additional failure
requires investigation. The local FreeBSD-labelled job compiles with Clang
on SUSE and checks FreeBSD dependency artifacts; it does not test native BSD.
Preserve failed attempts and explicit retry receipts instead of rewriting a
raw gate. A runtime utility fix must apply equally to baseline and patched jobs.

For a data package, load [edition-packaging](../edition-packaging/SKILL.md).
Check byte identity against every pinned upstream file, reproduce a fresh sync,
and verify that the package contains data and notices only. A local test deb
is not evidence of repository publication or installation on physical hardware.

Credit the authors from the touched upstream files and the projects providing
the profiles and CI machinery in [ATTRIBUTIONS](../../ATTRIBUTIONS.md).
Keep contact addresses out of the public contributor documentation.

## Rig packages

Use exact VID/PID rules and active-seat `uaccess` for hidraw. Never widen a
vendor to cover unknown products. A shared initialization PID does not identify
a wheel model. Keep it a candidate until the model is known. Stable drivers
may be selected by Hardware Setup; experimental drivers and Logitech's
replacement require an explicit choice matched to a detected device.
Install the running kernel's exact headers with its driver. Check whether
BTF-enabled headers require `pahole`; do not suppress BTF to hide that dependency.

Verify DKMS in an isolated source, state and install tree. Check the module's
name and vermagic, two kernel releases, autoinstall metadata, uninstall and
complete source-registration removal. For a replacement, require byte-exact
restoration of the matching kernel's stock module and an initramfs refresh.
Build source packages alongside every binary and unpack them independently.
Simulate the package transaction in fresh Debian testing with Sparky's official
repositories. Driver builds do not prove physical force-feedback effects.

Build OpenTrack with portable compiler flags and Qt 6. Preserve the individual
module licences and PS3 Eye's mixed MIT/GPL notices. State which SDK modules
were omitted and whether the optional Wine wrapper was built. A native package
without that wrapper does not establish Windows-game head tracking.
Load packaged UDP modules for a known six-component pose test over loopback.
Use OpenTrack's `with_tracker_teardown` guard when destroying plugin instances,
as its runtime does; ordinary deletion can reload already destroyed settings.
Keep page tests offscreen and inspect their captures before calling them proof.
