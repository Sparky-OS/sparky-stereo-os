# The boot menu: hidden, readable, under Secure Boot

Written by ORDER 572 (2026-11-14) after a fresh install on a notebook with Secure Boot on showed GRUB's menu for five seconds in tiny text, with a "?" in a box for the arrows, the frame and every accented letter.
Read the symptom first; the recipe and the rig command are at the end.

## The rules

- **One system: the menu is hidden and nothing waits. Another system found: the menu is shown.**
  Daniel, 2026-10-07: "dual boot found at install: os-prober on and menu shown; single OS: os-prober off, menu hidden"; 2026-11-14: "hidden grub, specially when there's only us installed", "if it has windows ok".
  The installer's dual-boot step runs os-prober once and, when it finds Windows or another Linux, writes `/etc/default/grub.d/sparky-stereo-dual-boot.cfg` (`GRUB_DISABLE_OS_PROBER=false`).
  At every `update-grub`, `30-sparky-stereo-boot.cfg` sets `GRUB_TIMEOUT_STYLE` and `GRUB_TIMEOUT`: os-prober on and a system found gives `menu` and 5 seconds; anything else gives `hidden` and 0.
  An os-prober that fails shows the menu and says so: never hidden on a guess.
- **The person's settings win.**
  `GRUB_TIMEOUT_STYLE`, `GRUB_HIDDEN_TIMEOUT`, or a `GRUB_TIMEOUT` other than Debian's 5 in `/etc/default/grub` are kept as they are, and `update-grub` says so; `SPARKY_STEREO_MENU=shown` in `/etc/default/sparky-stereo-boot` always shows the menu.
  Debian's `/etc/default/grub` always carries `GRUB_TIMEOUT=5`, so that value alone cannot be read as a choice.
- **The menu is never drawn without a loaded font.**
  A menu, a message or a prompt the person cannot read is a failure of the boot.
- **One text height on every screen** (4.2 mm, a monitor at a desk), from the screen's real size.

## Why the menu had "?" boxes: the font rule, with its clauses

- GRUB's Secure Boot verifier refuses every file type it does not list. GRUB 2.14, `grub-core/kern/efi/sb.c`, `shim_lock_verifier_init()`: kernels and chainloaded images are verified, a list of types (configuration, themes, pictures, translations) is skipped, and then `default: return grub_error (GRUB_ERR_ACCESS_DENIED, N_("prohibited by secure boot policy"));`. A font is in neither list.
  Proved at GRUB's command line under Secure Boot: `loadfont /boot/grub/fonts/NAME.pf2` answers `error: prohibited by secure boot policy.` and `lsfonts` lists nothing.
- The one font the signed GRUB loads is inside its own image. Debian's `debian/build-efi-images` copies `unicode.pf2` into `fonts/` of the memdisk it embeds, and `grub-core/font/font.c` opens a font given by a bare name from `(memdisk)` first: `file = try_open_from_prefix ("(memdisk)", filename);`, then from `$prefix/fonts`.
  So `loadfont unicode` works under Secure Boot and `loadfont /a/path.pf2` never does.
- Debian's `00_header` writes `if loadfont FONT ; then set gfxmode=...; load_video; insmod gfxterm; set lang=...; insmod gettext; fi` and then `terminal_output gfxterm` outside the `if`.
  With a refused font the graphical terminal starts with no font: GRUB's built-in ASCII glyphs (16 pixels high), a "?" in a box for everything else, no resolution set and no translation loaded, so the menu is also in English.
- That bundled font has one size, 16 pixels. The only way to give its text a height is the resolution GRUB shows the menu at.

What the edition does with that:

- `update-grub` under Secure Boot (the firmware's `SecureBoot` variable) names no font file. When 16 pixels is already the menu's height on the screen (a 24 inch full HD monitor), nothing else changes. On a denser screen the menu is given the resolutions at which 16 pixels has that height, nearest first, of the screen's own shape, then 1024x768, then the firmware's own; `SPARKY_STEREO_SECUREBOOT_TEXT=native` keeps the screen's resolution and small text.
- `/etc/grub.d/01_sparky_stereo_menu` adds, right after `00_header`: when `$shim_lock` is `y` or the font file is gone, `loadfont unicode`, that resolution, and the graphical terminal started again (`terminal_output console`, then `terminal_output gfxterm`); with no font at all, the firmware's text console. This is for Secure Boot switched on after the menu was written and for a person's own `GRUB_FONT`.
- At boot, `sparky-stereo-boot-check.service` compares Secure Boot with what the last `update-grub` recorded (`SECUREBOOT=` in `/var/lib/sparky-stereo-boot/grub-display`) and writes the menu again when it changed.
- Sized fonts under Secure Boot need a GRUB image that carries them, signed by a key shim trusts: the route Debian itself uses for its one font (a memdisk inside the signed image). That is the next piece, not a limit.

## The screen's size: two EDID fields

VESA E-EDID Release A2 (EDID 1.4):

- 3.6.2, bytes 15h and 16h (21 and 22): "The horizontal and vertical screen size parameters provide information on the screen dimensions of the display device, rounded to the nearest centimeter (cm)." and "The host (source) is expected to use this data to get a rough idea of the image size to generate properly scaled text and icons."
- 3.10.2, first detailed timing, bytes 12 to 14 (66 to 68 of the block): "Horizontal Addressable Video Image Size in mm" and "Vertical Addressable Video Image Size in mm", 12 bits each.

The rule: the screen size field decides the text's size; the detailed timing's millimetres are used when they say the same screen (within one centimetre of it); when the two differ the screen size field wins and `update-grub` says both.
A size is believed only when it can be a screen (at least 10 cm by 6 cm, an aspect between 1.2 and 2.6, not the 160 x 90 mm placeholder); a projector has both fields empty.
One notebook panel declared 29 x 17 cm in the first field (13.2 inches, right) and 344 x 193 mm in its timing (15.5 inches, wrong), and its text was sized for the wrong one.
The kernel knows the same fault as a quirk (`EDID_QUIRK_DETAILED_USE_MAXIMUM_SIZE`, `drivers/gpu/drm/drm_edid.c`: "Detailed timing descriptors have bogus size values, so just take the maximum size and use that").

## Traps

- **Symptom:** the menu shows tiny text, "?" boxes for arrows, frame and accented letters, and English help lines on a translated system.
  **Cause:** `GRUB_FONT` names a font file and GRUB runs under Secure Boot (or the file is gone).
  **Fix:** above.
  **Found by:** a screenshot of the menu through QMP, then `c` at the menu and `loadfont PATH`, `lsfonts`.
- **Symptom:** a test of the hidden menu passes on a menu that waits.
  **Cause:** judging `grub.cfg` alone. `timeout_style=hidden` with a timeout above 0 still waits.
  **Fix:** judge the screen: one screenshot every half second from power-on, and count the frames that show the menu's box.
- **Symptom:** a fresh install in the rig shows "another system" where there is none.
  **Cause:** os-prober finds the installer's own disk when it is a partition with a Linux root on it. It lists partitions only (`/sys/block/*/*[0-9]`).
  **Fix:** the rig's live system is one file system on the whole disk, with no partition table.
- **Symptom:** `secure-boot-fix` (SparkyLinux's installer step) fails in a rehearsal with `mkdir: cannot create directory '.../sys/fs/binfmt_misc'`.
  **Cause:** it finds the target with `mount | grep proc | grep calamares`, and a recursive bind of `/proc` puts a second mount under it.
  **Fix:** mount the target's `proc`, `sysfs`, `devpts` and `efivarfs` one by one, as Calamares' mount step does.
- **Symptom:** the installed guest boots but its root file system is read-only and `grub2-common.service` fails.
  **Cause:** the installer's `tmpfs /tmp` line in `/etc/fstab` against the edition's masked `tmp.mount` (ORDER 521). An SSD is what makes Calamares write that line: give the rig's target disk `rotation_rate=1` (`scsi-hd`), or the fault never shows.
  **Fix:** the installer's `tmpdisk` step and kernel-settings 20261111.1 or newer.
- **Symptom:** Calamares in a rehearsal stops at once: `Module "bootloader" requires "partition" before it in sequence`.
  **Fix:** the job that fills Calamares' storage (root mount point, partitions, firmware type, boot loader path) is a Python module named `partition`, found before the real one in `modules-search`.
- **Symptom:** the QEMU display never gives a sized font, whatever the resolution.
  **Cause:** QEMU's EDID always declares 100 dots per inch.
  **Fix:** `GRUB_STEREO_TEXT_MM` in the guest's `/etc/default/grub` stands in for a dense panel (7.2 gives the 28 pixels of a 13.3 inch full HD panel); the two-size rule is tested on EDID fixtures.
- **Symptom:** a direct kernel boot (`-kernel`) of the live system fails under OVMF with Secure Boot.
  **Cause:** OVMF verifies that kernel against `db`.
  **Fix:** the rig's variables carry the edition's public certificate in `db` and in `MokList` (`virt-fw-vars --add-db GUID CERT --add-mok GUID CERT`); a "reset motherboard" is the distribution's variables file as it ships, with Microsoft's keys only.
- **Symptom:** Hibernate is not offered in the guest although the swap line is right.
  **Cause:** Cushion Swap's generator offers it only when the area holds the RAM. **Fix:** a swap partition larger than the guest's memory.

## Recipe: a fresh install in the rig, without a window

1. Make the guest's root file system in an unprivileged container (`apt-get install` of the boot packages, the edition's kernel, Debian's signed shim and GRUB, `calamares` and the edition's installer settings), `docker export` it, drop `.dockerenv`, and turn the tar into a disk with `mke2fs -d root.tar` (needs libarchive).
2. Boot that disk as the installer's system (`-kernel`, `-initrd`, `root=LABEL=...`), with an empty target disk. A script partitions and formats it as the installer's partition step leaves it, copies the system as `unpackfs` does, and then runs the real Calamares with `QT_QPA_PLATFORM=offscreen calamares -d -c DIR`: `DIR/settings.conf` is the installed sequence cut to an `exec` phase of the steps that need no window and no network (`fstab`, the edition's shell steps, `grubcfg`, `bootloader`, the EFI fallback). A sequence that starts with `exec` runs by itself.
3. Boot the target alone under SeaBIOS, OVMF and OVMF with Secure Boot, take a screenshot every half second, and let a unit on the installed system write its facts (failed units, `/tmp`, `/proc/swaps`, the problems list, `CanHibernate`, `grub.cfg`'s timeout lines) to a small FAT disk the host reads with mtools.
4. One command repeats a row: `row.sh green sb windows` (firmware `bios`, `uefi` or `sb`; beside `none`, `windows` or `linux`). The published packages give the red control: `row.sh red sb none`.

## Credits

GRUB's font engine, graphical terminal and Secure Boot verifier (`grub-core/font/font.c`, `grub-core/term/gfxterm.c`, `grub-core/kern/efi/sb.c`): the GNU GRUB authors, as GRUB's own history records each change.
Debian's GRUB packaging, which bundles the font in the signed image (`debian/build-efi-images`): the Debian GRUB Maintainers; `debian/control` of 2.14-5 names Felix Zielcke, Jordi Mallach, Steve McIntyre, Julian Andres Klode and Mate Kukri.
os-prober: the Debian Installer team.
Calamares: Adriaan de Groot, Teo Mrnjavac and the Calamares contributors; the installer settings the edition builds on: Paweł "pavroo" Pijanowski.
