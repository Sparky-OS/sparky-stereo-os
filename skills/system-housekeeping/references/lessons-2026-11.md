# system-housekeeping: lessons from the lanes of 25 October to 6 November 2026

Harvested by ORDER 429 from the accepted lane reports; each line names the lane it came from.
A trap gives its symptom, its cause, its fix and how the cause was found; a recipe gives the commands and the result to expect.

## Recipes that worked

- Which mode did GRUB really hand over: on x86 `/sys/kernel/boot_params/data` is world-readable; the video type at offset 0x0f and width and height at 0x12 and 0x14 give the mode with `gfxpayload=keep` (0x70 at 1920x1080x32 matched the configured gfxmode). Use it for a boot check. (lane boot-no-fallbacks-345)
- Proof by user: as a normal user `--preview` lists only her own mailbox, dead.letter and msmtp queue; as root 13 expected paths. As a normal user `--clean system_mail.mailboxes` prints `Access denied: /var/mail/bob` and `Errors: 2` and leaves the files. CleanerML has no per-option condition (only `os` per action and `<running>` per cleaner), so a queue-of-removed-program option needs a generated file plus dpkg triggers or an upstream `unless_exe`. (lane bleachbit-system-mail-415)

## Traps: the symptom, the cause, the fix, how it was found

- Symptom: the skills helper's `link` would have cut a station from 31 skills to 7 core skills. Cause: the package gate compared `${Status}` with "ok installed", which dpkg never prints ("install ok installed"). Fix: query `${db:Status-Status}\n` (one word per architecture) and test with dpkg's own database through a private DPKG_ADMINDIR (two-architecture, held, removed-with-config cases): 42 of 42. The skill's system-housekeeping text mentions db:Status already (lane publish-qtmm12-skills-281)
- Symptom: bench tests of GRUB menu rewriting are red (7 FAILs, menu empty) or pass vacuously. Cause: Debian's `zz-update-grub` hook skips in containers, `grub-mkconfig` calls `${sbindir}/grub-probe` by full path, and in the C and C.UTF-8 locales glibc's gettext translates nothing whatever `LANGUAGE` says (German and English were the same string, so comparisons passed). Fix: run `update-grub` in the test, stub the probe at its own path, generate a locale (`localedef -i de_DE -f UTF-8 de_DE.UTF-8`) and set LANG to it. Found by: the first run's empty menu and English output after a correct merge. (lane kernel-keep-298)
- Symptom: initramfs-tools' `update-initramfs.conf` cannot be overridden. Cause: the file belongs to `initramfs-tools` (0.151), the switch is at update-initramfs lines 400-401, and there is no conf.d or environment override. Fix: divert it, but a conffile diverted in place cannot be renamed back on remove, so use a symlink at the original name plus the edition's own conffile beside it. Without a postrm rewrite the GRUB menu keeps merged translations until the next update-grub after the package is removed. (lane kernel-keep-298)
- Symptom: `grub-editenv` fails in a container ("failed to get canonical path of `overlay'") even on a valid file or `create`, while `grubenv.new` works. Cause: overlayfs. Fix: stub it in removal cases. Also: containers see the host's /sys/class/drm read-only, so `update-grub` in a container measures the host's screens through the edition's GRUB fragment. (lane boot-no-fallbacks-345)
- Symptom: sparky-beep tools open their window with exit 0 and no message when HOME is unusable, beep.conf unreadable or the tune folder unreadable (28 of 36 fail). Fix: one helper (beep_init_or_stop) runs init, reads the errors and prints the reason on the terminal, in the journal (logger -t) and in the program's own dialog (lane no-fallbacks-look-346f5)
- Symptom: a kept /home loses bleachbit.ini. Cause: the installer copies /etc/skel over a kept /home. Fix: the offered `--ignore-existing` copy. Found by: reading the installer step; not this package's fault. (lane bleachbit-system-mail-415)

## Perks of the part

- Scratch-folder triage: `du -x`, bounded find maxdepth 9; classify each folder as SAFE (published long ago, listed in a lane's `.artifacts`), KEEP (parked work, unpushed commits), NOT SAFE (a link gate's scratch, named "never touch" in briefs); a folder's size in notes may be wrong (22 GB, not 9.3 GB); keep only the cited 1 MB files. (lane k3d-parked-trees-381)

## Measured facts

- Debian's split for failing boot steps: a failed `update-grub` fails the package; a failed `grub-install` warns and continues (grub-efi-amd64, shim-signed); a service start never fails a package (debhelper `|| true`); kernel hooks run with `run-parts --exit-on-error`, so one failing hook stops the later ones. Debian's plymouth-quit unit ignores `plymouth quit`'s status; a drop-in that counts failure only while a splash still runs changes what `systemctl --failed` shows. (lane boot-no-fallbacks-345)

