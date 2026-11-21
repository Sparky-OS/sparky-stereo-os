# Taking over another package's configuration file

**For whoever makes a package of the edition change a setting that another package ships as a conffile.**
Written on 2026-11-21 (queue rows 629 and 802), with dpkg 1.23.11+stereo3d3, Debian Policy 4.7.4.1 and Debian testing of that day.

## The rule, at its source

- Debian Policy 4.7.4.1, appendix 7 ("Diversions - overriding a package's version of a file"): "Do not attempt to divert a conffile, as dpkg does not handle it well. Do not use diversions for files that have their own native override mechanisms, such as systemd unit files."
- Debian Policy 10.7.4 ("Sharing configuration files"): "Neither alternatives nor diversions are likely to be appropriate in this case; in particular, dpkg does not handle diverted conffiles well." and "The maintainer scripts must not alter a conffile of any package, including the one the scripts belong to."
- Debian Policy 3.9 (maintainer scripts): "You should not use dpkg-divert on a file belonging to another package without consulting the maintainer of that package first."
- dpkg-divert(1) of dpkg 1.23.11: diversions are for "some package's configuration file, or whenever some files (which aren't marked as conffiles) need to be preserved by dpkg"; `--rename` "will abort operation in case the destination file already exists".

So the first question is always what the owning package offers: a drop-in folder, a file its own file reads, a variable, a program, a native override (a systemd drop-in).
Only where the owning package offers nothing is a diversion left, and then the edition's dpkg-stereo must judge it ([lean-code, a file under a dpkg diversion](../../lean-code/references/diverted-files.md)).

## What dpkg does with a diverted conffile, measured

- **The owning package's conffile is never installed** when the owning package is unpacked in the same dpkg run as the package that diverts it, before that package's preinst.
  dpkg unpacks a conffile as `NAME.dpkg-new` and installs it at configure; the diverting package's own file at `NAME` is extracted through the same `NAME.dpkg-new` and replaces it.
  Seen on the published edition: `dpkg-query -W -f '${Conffiles}' initramfs-tools nano` gives `/etc/initramfs-tools/update-initramfs.conf newconffile` and `/etc/nanorc newconffile`, and neither Debian file is anywhere on the system (`dpkg.log`: initramfs-tools and nano installed one second before sparky-stereo-boot and sparky-stereo-console).
- **A diverted conffile was taken for the person's edit.** With dpkg-stereo 0.1.41 and 0.1.42, `--verify` read the owning package's record on the diverting package's file; when the owning package is upgraded and its conffile changed, dpkg asked "Modified locally since installation" (no terminal: exit 1, `.dpkg-new` left).
  0.1.43 reads the owning package's copy where dpkg keeps it, and the same upgrade settles with no question.

## What each owner offers (Debian testing, 2026-11-21)

| Path | Owning package | What the owning package reads besides it | Form for the edition |
|---|---|---|---|
| `/etc/skel/.bashrc` | bash 5.3-4 | its `.bashrc` sources `~/.bash_aliases` ("You may want to put all your additions into a separate file like ~/.bash_aliases") | our own `/etc/skel/.bash_aliases`, for new accounts, as the `.bashrc` is |
| `/etc/nanorc` | nano 9.3-1 | nothing system-wide: `include` takes syntax definitions only (nanorc(5): "syntaxfile may contain only the above commands, from syntax to icolor"); then the person's own nanorc | none: stays a diversion |
| `/etc/zsh/zshrc` | zsh-common 5.9.2-1 | nothing; then the person's `~/.zshrc` | none: stays a diversion |
| `/etc/initramfs-tools/update-initramfs.conf` | initramfs-tools 0.151 | nothing: `CONF=/etc/initramfs-tools/update-initramfs.conf`, `[ -r ${CONF} ] && . ${CONF}`, no folder, no environment, no program | none: stays a diversion |
| `/etc/issue`, `/etc/issue.net`, `/etc/update-motd.d/10-uname` | base-files (SparkyLinux's, carried through Lean Code) | agetty reads `--issue-file` and `/etc/issue.d/` after `/etc/issue`; sshd's `Banner` names any file; pam_motd runs every script of `/etc/update-motd.d` | see the row's notes in the hand-back: a banner file of our own for SSH; the console's other two need a choice |
| `/etc/grub.d/10_linux` | grub-common 2.14-5 | `/etc/grub.d/` takes scripts of our own; GRUB runs every function a later script defines | the boot menu's own script (system-housekeeping, boot-menu) |

## Removing a diversion in a successor, keeping the person's edit

Measured on 2026-11-21 with fixture packages (a conffile owner; a diverting package whose 1.0 puts a link or a plain file at the path and diverts the owning package's copy with `--rename`; a 2.0 that ships nothing there):

| 2.0 removes the diversion in | The owning package's file afterwards |
|---|---|
| its preinst (before dpkg unpacks 2.0) | **gone**: dpkg removes the path as a file of the old version that the new one no longer ships, and it is now the owning package's file (`dpkg -S` still names the owning package; `--verify` says MISSING) |
| its postinst (configure) | back at its name, a person's edit of it kept; nothing left at the diverted name; `--verify` clean, or `CHANGED` for the person's edit |

So the successor removes the diversion in its postinst: if the path is still its own link (or its own unchanged file), remove it, then `dpkg-divert --package NAME --remove --rename --divert DIVERTED PATH`.
Between the unpack and that postinst the path does not exist; a program that reads it in that window (a kernel's `update-grub` run by a package configured earlier in the same dpkg run) sees no file, so a successor whose file feeds a generated configuration runs the generator again at the end of its postinst.
A person's edit of the diverting package's own file at the path is not kept by this by itself: dpkg removes that file at the unpack. Not measured yet: saving it in the successor's preinst and putting it back over the owning package's copy (the owning package's copy then waits as `PATH.dpkg-dist`).

## Traps

- **Symptom:** `dpkg-stereo --verify` says `CHANGED PATH (changed by the person)` on an untouched system, for a path one of our packages diverts.
  **Cause:** the verifier read the owning package's record at the path; fixed in dpkg-stereo 0.1.43.
  **How found:** the published edition installed as the round installs it; `dpkg-divert --list` beside `records/*.tsv`.
- **Symptom:** a conffile of the owning package is in `newconffile` state and its file is nowhere.
  **Cause:** above (the shared `.dpkg-new` name). **Fix:** do not divert a conffile. Not measured: whether a package that makes its file at the path in its postinst, instead of shipping it, avoids the loss.
  **How found:** the step 1 table of rows 629/802: the owning package's copy absent at the diverted name, then `dpkg-query ${Conffiles}` and `dpkg.log`.
- **Symptom:** after the upgrade that drops a diversion, the owning package's conffile is missing (`dpkg -S` names the owning package, `--verify` says MISSING), with no error from dpkg.
  **Cause:** the successor removed the diversion in its preinst; at the unpack dpkg removed the path as a file the old version shipped and the new one does not, and that was now the owning package's file.
  **Fix:** remove the diversion in the postinst. **How found:** fixture packages, both shapes (a link, a plain file), with and without a person's edit, both places (the table above).
