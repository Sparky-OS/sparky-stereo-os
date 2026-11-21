# The boot menu: hidden, readable, under Secure Boot

Written by ORDER 572 (2026-11-14) after a fresh install on a notebook with Secure Boot on showed GRUB's menu for five seconds in tiny text, with a "?" in a box for the arrows, the frame and every accented letter.
Read the symptom first; the recipe and the rig command are at the end.

## The rules

- **One system: the menu is hidden and nothing waits. Another system found: the menu is shown.** `sudo sparky-stereo-boot menu` shows a hidden menu once, at the next start.
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
- **Symptom:** on a Korean system that lists another system, `update-grub` stops with `/etc/grub.d/30_os-prober: 263: printf: %2$: invalid directive` and the menu is not written (a kernel update then fails too).
  **Cause:** GRUB's shell scripts print their messages with the shell's `printf` (`gettext_printf` in `grub-mkconfig_lib`, under `/bin/sh`), which has no reordered arguments; the Korean translations of "Found %s on %s" use `%2$s`. Debian's own catalogue leaves the shell messages out, so only the edition's supplemental catalogue (`sparky-stereo-grub-l10n`) brought them in.
  **Fix:** the supplemental catalogue leaves out a shell message whose translation reorders its arguments (`msggrep --invert-match --msgstr -e '%[0-9][0-9]*\$'`), and its build stops if one is left.
  **Found by:** running `update-grub` in each of the ten languages on a guest beside Windows and reading the menu's `set lang=`: Korean still said Japanese, the language of the run before.
- **Symptom:** the person holds Shift or presses Esc and the hidden menu does not open.
  **Cause:** with `timeout=0` GRUB looks at the keyboard once. In QEMU, Shift held and Esc pressed through the start opened nothing under SeaBIOS and plain OVMF; only a run of Esc presses under Secure Boot (a slower start) landed.
  **Fix:** never tell the person to use a key. `sudo sparky-stereo-boot menu` sets `sparky_menu_once` in GRUB's environment block and the next start shows the menu for 30 seconds; the boot sets it by itself when a Secure Boot key waits for its enrolment, the menu is shown when shim refuses the newest kernel, and it shows by itself after a start that did not finish (below).
- **Symptom:** beside Windows the menu stays hidden although the installer turned os-prober on.
  **Cause:** `grub-mkconfig` sources `/etc/default/grub.d/*.cfg` in name order, and `sparky-stereo-dual-boot.cfg` comes after `30-sparky-stereo-boot.cfg`, which therefore still saw os-prober off.
  **Fix:** the fragment reads the last `GRUB_DISABLE_OS_PROBER=` of the other files itself.
  **Found by:** the rig's dual-boot rows failing while every fixture test passed; the installer's log said "shown" at `grub-install` and "hidden" at `grub-mkconfig`.
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

## After a start that did not finish

Written by ORDER 572b (2026-11-15).
A hidden menu with no wait opens with no key, so a newest kernel that no longer starts left no way to the older one.
Daniel, 2026-11-15: "I agree with your idea after a failed start, alongside the check filesystem".
Now, after a start that did not finish, the menu shows by itself at the next start, the file systems are checked at that start, and the person is told at login; every start that follows a finished one stays hidden with no wait.

### The mechanism is GRUB's own, and Debian carries it switched off

Look before you build: `grep -n recordfail /etc/grub.d/* /boot/grub/grub.cfg` on any Debian system.

- `00_header` writes `function recordfail { set recordfail=1; ... save_env recordfail ... }` and `10_linux` writes the call `recordfail` at the top of each entry, both only `if [ "$quick_boot" = 1 ]`.
  `quick_boot="@QUICK_BOOT@"` is set when GRUB is configured (`debian/patches/quick-boot.patch`: `AC_ARG_ENABLE([quick-boot]`), and `debian/rules` passes `--enable-quick-boot` only inside `ifeq (yes,$(shell dpkg-vendor --derives-from Ubuntu && echo yes))`.
  On Debian the three scripts say `quick_boot="0"`, and no setting reaches it.
- What is there on Debian all the same: `00_header`'s `make_timeout` always writes `if [ "${recordfail}" = 1 ] ; then set timeout=${GRUB_RECORDFAIL_TIMEOUT:-30} else ...`, and `grub2-common.service` (enabled) runs `grub-editenv /boot/grub/grubenv unset recordfail` with `Requires=boot-complete.target`, `After=boot-complete.target` and the sleep targets.
  So a generated `grub.cfg` has the test at its top and nothing that ever sets the flag.
- With the flag set, the hidden style is not applied (it is in the `else` branch), and GRUB shows the menu: `grub-core/normal/menu.c`, `get_timeout_style()`: "If the variable "timeout_style" is not set or invalid, default to TIMEOUT_STYLE_MENU".

What the edition adds (`sparky-stereo-boot` 0.1.11):

- `/etc/grub.d/01_sparky_stereo_menu` writes the function, and while the flag is set: `timeout_style=menu`, the time, and `sparky_stereo_check="fsck.mode=force sparky_stereo.start=unfinished"`, which the kernel line of every Linux entry carries through `GRUB_CMDLINE_LINUX`.
- The call, since 0.1.13 (rows 629/802), with no diversion: Debian's `10_linux` writes `load_video` into each of its entries, recovery included, unless `GRUB_GFXPAYLOAD_LINUX=text` (its lines 124 to 128 in 2.14-5).
  GRUB runs the last definition of a function (`grub-core/script/function.c`) and sets `chosen` to the entry's id, `parent>child` inside a submenu, before it runs the entry (`grub-core/normal/menu.c`).
  So `01_sparky_stereo_menu` takes `00_header`'s own `function load_video { ... }` from its output at `update-grub` time (its body depends on `GRUB_VIDEO_BACKEND` and `GRUB_FORCE_EFI_ALL_VIDEO`), writes it again as `sparky_stereo_load_video`, and writes a `load_video` that calls `recordfail` when `regexp '^gnulinux-' "${chosen}"` matches, then that body.
  `regexp` is in Debian's signed image (`build-efi-images`).
  `00_header`'s own font lines call `load_video` before any entry runs, with `chosen` unset, so they record nothing.
  `90_sparky_stereo_start` runs `00_header` and `10_linux` once more and keeps the problem LOCAL97 when a Linux entry (one with a `linux` line) has no `load_video`, or `00_header` writes none; it clears it otherwise.
  Up to 0.1.12, `/etc/grub.d/10_linux` was a link to a program that ran Debian's file, diverted to `/etc/sparky-stereo-boot/10_linux.debian`; Debian Policy, appendix 7, says "Do not attempt to divert a conffile", and dpkg-stereo read the diverted file as changed by the person. 0.1.13's postinst gives it back (edition-packaging, `taking-over-a-configuration-file.md`).
  Only the Linux entries record a start: an entry of another system (Windows, another Linux) is `osprober-...` and must not, or every start of Windows would count as one of ours that did not finish.
  Proved at boot in QEMU (rows 629/802), under OVMF with Secure Boot on and Debian's signed GRUB (the ESP's `grubx64.efi` has the hash of grub-efi-amd64-signed 1+2.14+5's image), after an upgrade from 0.1.10: `regexp` runs in the signed image, `chosen` is set for the default entry of a hidden menu with no wait (a power cut 1.5 s into the kernel brings the menu at the next start), and a start from inside "Advanced options" records itself too (`chosen` is `gnulinux-advanced-...>gnulinux-...`: the older kernel picked there and cut, the next start shows the menu and carries the forced check).
  On a BIOS start GRUB's `i386-pc` image loads `regexp` as a module at its first use, and the same power cut brings the menu.
  Beside Windows the menu keeps its 5 seconds at a normal start and after an unfinished one; ten normal starts each of 0.1.10 and 0.1.13, in turns, show no menu frame and the same time to the kernel (median 2.786 s and 2.787 s).
  A generated `grub.cfg` reads: 00_header's `function load_video`, its font block's call (Debian's body, before any entry), then 01's `function sparky_stereo_load_video` and the recording `function load_video`, then `load_video` in each of 10_linux's entries, recovery included.
- **With `GRUB_GFXPAYLOAD_LINUX=text` no start can be recorded, and the person is told.**
  Debian's `10_linux` then writes no function call into its entries at all (only `set gfxpayload=$linux_gfx_mode`, `insmod`, `echo`, `linux`, `initrd`, all commands, which a function cannot replace), so `update-grub` keeps LOCAL97 and the login says it; a start that does not finish then brings no menu and no forced check (measured).
  `sparky-stereo-boot repair` runs `update-grub` again, which keeps the problem while the setting stays ("Still failing: update-grub (exit status 0)").
- `/etc/grub.d/90_sparky_stereo_start` adds the menu's last entry, there only while the flag is set, with the reason as its title in the system's language.
  It is the last one so that no other entry changes its number (a person's `GRUB_DEFAULT=2` keeps meaning the same entry).
- The time: the person's `GRUB_RECORDFAIL_TIMEOUT` when set; otherwise a menu that is shown anyway keeps its time, and a hidden one is shown for 30 seconds, GRUB's default for it.
- `sparky-stereo-boot-finished.service` (after `boot-complete.target`, and after a resume) clears the flag wherever it is kept, and after an unfinished start reads what the check found and hands it to the problems engine for the login.
- `SPARKY_STEREO_UNFINISHED_START=no` in `/etc/default/sparky-stereo-boot` turns all of it off.

### What counts as not finished

systemd.special(7), `boot-complete.target`: "Order units that are required to succeed for a boot process to be considered successful before this unit and add a Requires= dependency from the target unit to them."
Debian's unit clears the flag after that target, which by itself needs only `sysinit.target`.
The edition adds `sparky-stereo-boot-login.service`, `Before=boot-complete.target`, `After=display-manager.service`, required by the target: a start whose login screen's service failed to start has not finished.
So a kernel panic, a boot image that cannot mount the root, the emergency shell, a hang before the basic system is up, a login screen that fails to start and a power cut on the way all show the menu at the next start.
A login screen that runs and shows nothing counts as finished: nothing in the system can see that.
A start into recovery mode never reaches the target either, so the start after it shows the menu.
A plain reboot and a resume from hibernation do not count: the resumed system clears the flag (the unit is wanted by `hibernate.target`, as Debian's is).
Never order that unit after a target: `multi-user.target` waits for `grub2-common.service`, which waits for `boot-complete.target`, so `After=multi-user.target` or `After=graphical.target` on a unit before `boot-complete.target` is an ordering cycle, and systemd drops a job to break it.
Check a display manager's unit before trusting the order: sddm, plasmalogin, lightdm, gdm3, greetd and lxdm in Debian testing are ordered after `systemd-user-sessions.service`, a getty and Plymouth's quit, none after a target.

### The check

- `fsck.mode=force` on the kernel line (systemd-fsck@.service(8): "force unconditionally results in full file system checks").
  initramfs-tools reads the same word (`init`: `forcefsck|fsck.mode=force`) and checks the root with `fsck -f -a` from the boot image; its log is `/run/initramfs/fsck.log`, written by `logsave`, which adds `fsck exited with status code N` for any status other than 0.
  A root the boot image did not check (no `fsck` in it, another generator) is checked by `systemd-fsck-root.service`.
  The other file systems of `/etc/fstab` with a pass number above 0 are checked by `systemd-fsck@NODE.service`, and NODE is the node systemd derives from the fstab field: `UUID=F1A5-69B3` is `/dev/disk/by-uuid/F1A5-69B3`, so the unit is `systemd-fsck@dev-disk-by\x2duuid-F1A5\x2d69B3.service` (`systemd-escape --path --template=systemd-fsck@.service NODE`), never the kernel's device name.
  Its lines are in the journal of that unit.
- fsck(8): exit status 1 is "Filesystem errors corrected", 4 "Filesystem errors left uncorrected".
- btrfs and xfs have no check at boot: `fsck.btrfs` and `fsck.xfs` do nothing by design, the type checks itself when it is mounted. The message names them as such.
- A resume from hibernation is safe: the boot image tries the resume before it checks or mounts the root.

### Where GRUB cannot write the flag

Debian's own rule, `check_writable` in `00_header`: the abstractions `diskfilter` and `lvm` (RAID, LVM) under `/boot/grub`, and the types `btrfs | cpiofs | newc | odc | romfs | squash4 | tarfs | zfs`.
GRUB reads those and cannot write them, so `save_env` does nothing there.

- On UEFI the flag goes to an environment block on the EFI system partition (`EFI/sparky-stereo-boot/grubenv`): FAT on a plain partition, which GRUB writes.
  `update-grub` makes the block (`grub-editenv FILE create`) and says so; GRUB finds the partition by its UUID, `load_env -f` and `save_env -f`.
- On a BIOS start there is no such place.
  `update-grub` says that the menu cannot show by itself on this computer and names `SPARKY_STEREO_MENU=shown`; nothing is written into the entries.
- Ubuntu's answer for that case (`quick-boot-lvm.patch`) is a menu shown for 30 seconds at every start on UEFI. The edition does not take it: nothing may add a wait to a normal start.

### Breaking a start in the rig

Each row boots a copy-on-write disk (`qemu-img create -f qcow2 -b BASE -F raw`) over one installed base per firmware, so a broken guest costs nothing.

- A kernel that panics: overwrite the newest kernel's boot image with random bytes (keep a copy); the kernel stops with "VFS: Unable to mount root fs".
- A start that hangs: a unit with `DefaultDependencies=no`, `Before=sysinit.target`, `Type=oneshot`, `TimeoutStartSec=infinity`, that removes its own link first and then sleeps for ever, so only one start hangs.
- A power cut on the way: kill QEMU a moment after the kernel's first line on the serial port.
  The kernel line needs `console=ttyS0 earlycon=uart8250,io,0x3f8,115200 ignore_loglevel`, or `quiet` keeps the first line off the port.
- A damaged root that only a forced check finds: make a file, `sync`, `fsfreeze -f /; fsfreeze -u /` (the journal is written out to its final place), `echo 3 > /proc/sys/vm/drop_caches`, `debugfs -w -R "sif FILE links_count 5" DEVICE` on the mounted root, then the power cut.
  Without the freeze the journal's replay at the next start puts the good inode back and the check finds nothing but the replay.
- A start from inside "Advanced options" that does not finish: `sparky-stereo-boot menu`, then at the next start the keys to the older kernel and the power cut 1.5 s after its first line (`RIG_CUT_ON` with the keys in one boot); the start after must show the menu, and its kernel line must carry `fsck.mode=force`, which only a set flag adds (the menu asked for once shows anyway).
- The older kernel from the menu: Down, Enter (the submenu), Down, Down, Enter.
  Send the keys only once the menu is on the screen (two seconds of screenshots that show its box), and take a screenshot after each key: under Secure Boot the firmware takes 14 to 20 seconds on a busy machine, and a key sent by the clock lands on the wrong line.
- A login screen that fails to start: a unit whose program does not exist, linked as `display-manager.service` and wanted by `multi-user.target`.
- A plain reboot and a hibernation each need the same small disk for the guest's notes across both runs of the virtual machine.
- Judge the screen as before: a screenshot every half second, and count the frames that show the menu's box.
- The time GRUB takes: from QEMU's start to the kernel's first line on the serial port, ten starts each for the old and the new package, in turns (old, new, old, new) on two disks over the same base, and judged start by start. On a shared machine the same package's starts differ by a second and more, so ten starts of one and then ten of the other measure the machine's other work.

### Traps

- **Symptom:** under Secure Boot, Enter on "Advanced options" starts the newest kernel, which stops in "VFS: Unable to mount root fs on unknown-block(0,0)"; the submenu never opens and the older kernel cannot be reached.
  **Cause:** something loaded a kernel while GRUB read the menu (the edition's own check that asks shim about the newest kernel, `linux KERNEL` inside an `if`), and GRUB starts whatever is loaded when Enter is pressed on a submenu or on an entry that loads nothing: `grub-core/normal/menu.c`, `grub_menu_execute_entry`: "Implicit execution of boot, only if something is loaded" comes before `grub_show_menu` for the submenu. The kernel started that way has no boot image and no kernel line.
  **Fix:** never leave a kernel loaded when the menu will be shown. GRUB has no command that unloads; its EFI loader calls `grub_loader_unset()` right after the file it is given opens (`grub-core/loader/efi/linux.c`), so `linux` on a file shim accepts that is no kernel (MokManager beside shim) unloads and then fails. The line that prints is gone when the menu is drawn, so do it only when the menu will be shown.
  **Found by:** a screenshot after each key: the frame after Enter was black and the next one the kernel's panic, with the intact newest kernel. Then GRUB's source.
- **Symptom:** the login note says "no trace of a check was found" although the journal has the check's lines.
  **Cause:** the result was looked for in the boot image's log only, or under a unit named after the kernel's device name. A boot image without `fsck` leaves the root to `systemd-fsck-root.service`, and the other units are named after the fstab field's node.
  **Fix:** the boot image's log, else `systemd-fsck-root.service`; the others by the node (above).
  **Found by:** a fresh install in the rig, whose installer run leaves out the installer's boot image step: the journal of that start had both checks.
- **Symptom:** a repaired root is reported as clean.
  **Cause:** `logsave` of e2fsprogs 1.47 writes "fsck exited with status code 1"; older ones wrote "died with exit status".
  **Fix:** read both.
- **Symptom:** the older kernel, started from "Advanced options", gets no forced check, and a start from that submenu is not recorded.
  **Cause:** `submenu` opens a new context that keeps only exported variables (`grub-core/normal/context.c`, `grub_env_new_context`: `if (var->global || export_all)`). `have_grubenv`, `boot_once` and any variable set in the header are gone inside it; functions stay.
  **Fix:** `export` every variable an entry or the function reads.
  **Found by:** reading `context.c` before the first rig run, then the kernel line of the older kernel in the guest.
- **Symptom:** after one start of Windows the menu says our last start did not finish.
  **Cause:** the flag set for every entry, or in the header.
  **Fix:** only the Linux entries call `recordfail`.
- **Symptom:** the start after the repaired one stops again in the same panic.
  **Cause:** the rig started the older kernel and left the newest kernel's boot image broken.
  **Fix:** the row's command on the older kernel puts the boot image back, as a person would.
- **Symptom:** in a rig run the keys never reach the menu and it starts the default entry.
  **Cause:** the rig's timeline runs its steps one after another, and a run of screenshots covered the seconds of the keys.
  **Fix:** screenshots up to the keys, the keys, then screenshots again.
- **Symptom:** two rows side by side fail at random ("the upgrade did not install").
  **Cause:** helper containers with a fixed name; each row removed the other's.
  **Fix:** the row's process number in every helper's name.
- **Symptom:** the engine answers "called ... with arguments or details it cannot read" and the problem is not kept.
  **Cause:** `repair=` takes a list of commands, each a list of words.
- **Symptom:** `systemd-analyze blame` shows 0.9 s for a unit ordered before `boot-complete.target`.
  **Cause:** it started Python to ask systemd one question; `multi-user.target` waits for it.
  **Fix:** a shell program (`systemctl show -p LoadState -p ActiveState display-manager.service`).
- **Symptom:** the installer stops at its `fstab` step on a btrfs root in the rig: `TypeError: 'NoneType' object is not iterable`.
  **Cause:** the step reads `btrfsSubvolumes` from the installer's storage, which the mount step fills.
  **Fix:** the rig makes the subvolume `@`, mounts the root from it and puts `[{"mountPoint": "/", "subvolume": "/@"}]` in the storage, as the installer's own mount step does.
- **Symptom:** a rig check "no diversion of 10_linux" passes on a system that has one.
  **Cause:** the guest's dpkg speaks the system's language: `dpkg-divert --list` prints "desvio de ..." on a pt_BR guest, so a grep for "diversion of" never matches.
  **Fix:** `LC_ALL=C dpkg-divert --list` and `LC_ALL=C dpkg -S` in the guest's commands.
  **Found by:** reading the guest's `cmd.log` beside the passing check.
- **Symptom:** "no forced check on the kernel line" fails on a start whose kernel line has none.
  **Cause:** the facts file also quotes `grub.cfg`, whose header always defines `sparky_stereo_check="fsck.mode=force ..."`.
  **Fix:** read the `== cmdline` line of that start only; a check is shown able to fail by running it on a row that did carry the check.
- **Symptom:** lintian prints `systemd-service-file-refers-to-unusual-wantedby-target` twenty times for one unit.
  **Cause:** sleep targets in the unit's `[Install]` line, counted once per link.
  **Fix:** the package ships the links in the targets' `.wants` folders; `[Install]` names `multi-user.target` only.

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
GRUB's recordfail ("If the previous boot failed ... then show the boot menu regardless", `debian/patches/quick-boot.patch` in Debian's grub2): Colin Watson, with Richard Laager and Robie Basak named as authors in the patch; the case where GRUB cannot write its environment block (`quick-boot-lvm.patch`): Steve Langasek.
`boot-complete.target`, `systemd-fsck` and `fsck.mode=`: the systemd authors. The root check in the boot image: the Debian kernel team's initramfs-tools. `e2fsck` and `logsave`: Theodore Ts'o and the e2fsprogs contributors.
The rig this section's rows run in: lane 572 of the edition.
