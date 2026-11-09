# GRUB: every way the edition's configuration makes GRUB print an error

Written by ORDER 472 (2026-11-08) after a person saw an error on a television during GRUB and the words were not kept.
Read the symptom first: GRUB's messages go by in one or two seconds when the menu is hidden, and the kernel's first frames cover them.

## Recipe: boot a generated grub.cfg and read GRUB's own words

1. Take a generated `/boot/grub/grub.cfg` (00_header with the edition's `30-sparky-stereo-boot.cfg` and the artwork fragments applied, 05_debian_theme, 06_sparky_theme, the first entry of 10_linux).
2. Build a GPT disk without a loop device: an ESP with `mformat` and `mcopy`, an ext2 root with `mke2fs -d TREE -E offset=...` and the root's UUID the cfg names, `grub-mkimage -O x86_64-efi -p '(hd0,gpt2)/boot/grub'` as `EFI/BOOT/BOOTX64.EFI`, the modules and `fonts/unicode.pf2` copied into `/boot/grub` as grub-install does.
3. Boot it in QEMU with OVMF (software emulation is enough), `-serial file:serial.log`, and put `serial --unit=0`, `terminal_input serial console` and `terminal_output serial gfxterm` at the top of the cfg: GRUB then writes every message to the file, where a screen dump would show only the last frame.
4. The test is `sparky-stereo-boot`'s `tests/grub-errors/run-tests.sh IMAGE KERNEL ART.png`: fourteen cases, each compared with `expected.txt` (the messages, how many times, and whether GRUB stops at "Press any key to continue...").

## What GRUB 2.14 printed (QEMU, OVMF, a generated grub.cfg)

| A state of the machine | GRUB's words | Stops for a key? |
| --- | --- | --- |
| A background picture a package took away after the last update-grub (00_header, 05_debian_theme and 06_sparky_theme each name it) | `error: file `/opt/artwork/sparky-black.png' not found.` three times | no, boots on |
| The picture cut short, or not a PNG | `error: png: unexpected end of data.` or `error: png: not a png file.`, three times | no |
| The root's UUID in grub.cfg gone (cloned disk, partition made again) | `error: no such device: UUID.` four times, then the entry fails | yes |
| The kernel the first entry names removed before update-grub wrote the menu again | ``error: file `/boot/vmlinuz-X' not found.`` then `error: you need to load the kernel first.` | yes; with a second entry also "Failed to boot both default and fallback entries." |
| The boot image removed | ``error: file `/boot/initrd.img-X' not found.`` | yes |
| The menu font (`sparky-NN.pf2` of `GRUB_FONT`) removed | ``error: file `/boot/grub/fonts/sparky-30.pf2' not found.`` | no |
| `grubenv` overwritten | `error: invalid environment block.` | no |
| The edition's `${sparky_stereo_boot}` set (plymouth.stereo, video=), a gfxmode list ending in `auto`, a saved or next entry that no longer exists, a default beyond the last entry | nothing: GRUB boots the first entry | no |

Reading it for a person: a missing or damaged picture is a flash of text on the way to the kernel; a missing kernel, boot image or UUID is the one that stays and waits.
Both read as "an error on the image" on a screen that is not the one the person looks at.

## Traps

- Symptom: the same error line three times. Cause: Debian's 00_header, 05_debian_theme and desktop-base's or Sparky's 06_sparky_theme each load the background (`background_image`, and 05 and 06 inside an `if`, which still prints the error). Fix: none needed in the cfg; the cure is that the picture exists, so a package that owns a picture GRUB names runs `update-grub` when it changes or goes (sparkyos-artwork does). Found by: the serial log of a case with the picture removed.
- Symptom: a test for the error finds nothing, the screen shows a normal menu. Cause: the kernel starts within seconds and covers GRUB's lines, and a screen dump taken later is the kernel's. Fix: read GRUB's serial output. Found by: eight cases with identical dumps and different serial logs.
- Symptom: the control case itself prints ``error: file `/boot/grub/fonts/unicode.pf2' not found.`` Cause: a generated cfg sets `feature_default_font_path`, so GRUB looks for the font in `$prefix/fonts`; a hand-made test disk has none. Fix: copy the font there as grub-install does.
- Symptom: a 200 MB sfdisk disk is refused by OVMF. Cause: `mformat -F` makes FAT32 on a 32 MiB ESP, which has too few clusters. Fix: let mformat choose.
