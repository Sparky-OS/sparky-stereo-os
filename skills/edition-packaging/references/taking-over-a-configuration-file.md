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
| `/etc/skel/.bashrc` | bash 5.3-4 | its `.bashrc` sources `~/.bash_aliases` ("You may want to put all your additions into a separate file like ~/.bash_aliases") | our own `/etc/skel/.bash_aliases`, for new accounts, as the `.bashrc` is (sparky-stereo-console 20261121; below) |
| `/etc/nanorc` | nano 9.3-1 | nothing system-wide: `include` takes syntax definitions only (nanorc(5): "syntaxfile may contain only the above commands, from syntax to icolor"); then the person's own nanorc | none: stays a diversion |
| `/etc/zsh/zshrc` | zsh-common 5.9.2-1 | nothing; then the person's `~/.zshrc` | none: stays a diversion |
| `/etc/initramfs-tools/update-initramfs.conf` | initramfs-tools 0.151 | nothing: `CONF=/etc/initramfs-tools/update-initramfs.conf`, `[ -r ${CONF} ] && . ${CONF}`, no folder, no environment, no program | none: stays a diversion |
| `/etc/issue`, `/etc/issue.net`, `/etc/update-motd.d/10-uname` | base-files (SparkyLinux's, carried through Lean Code) | agetty reads `--issue-file` and `/etc/issue.d/` after `/etc/issue`; sshd's `Banner` names any file; pam_motd runs every script of `/etc/update-motd.d` | see the row's notes in the hand-back: a banner file of our own for SSH; the console's other two need a choice |
| `/etc/grub.d/10_linux` | grub2-common 2.14-5 | `/etc/grub.d/` takes scripts of our own; GRUB runs every function a later script defines | the boot menu's own script (system-housekeeping, boot-menu) |

## A diversion that stays: the safe form

Where the owning package offers nothing, the diversion stays, and its preinst must keep the owning package's conffile.
The loss happens when apt unpacks the owning package in one dpkg call and ours in a later call of the same run: the owning package's conffile waits as `PATH.dpkg-new`, our preinst adds the diversion (nothing to rename yet), and our own `PATH` is unpacked through that same `PATH.dpkg-new`.
So, in the preinst, right after `dpkg-divert --add --rename`:

```sh
before=$(dpkg-divert --listpackage "$f")      # read before the --add
dpkg-divert --quiet --package "$package" --add --rename --divert "$f.debian" "$f"
if [ -z "$before" ] && [ -e "$f.dpkg-new" ] && [ ! -e "$f.debian.dpkg-new" ]; then
    mv "$f.dpkg-new" "$f.debian.dpkg-new"     # where dpkg now installs the owning package's copy
fi
```

and the postrm does the reverse after `--remove --rename` (`$f.debian.dpkg-new` back to `$f.dpkg-new`), and removes only a diversion `--listpackage` says is its own.
Only in the run that adds the diversion: once it exists, the owning package's unpack already goes to the diverted name.
Measured (rows 629/802): fixture packages in four install orders (one apt run, one dpkg call either way round, two dpkg calls), sealed with Lean Code or not, keep the owning package's conffile only in this form; with the real packages, nano and sparky-stereo-console in one `apt-get install` on the published edition (apt unpacked nano, then the console, then zsh-common), the published console leaves `/etc/nanorc newconffile` with nothing at `/etc/nanorc.debian`, and sparky-stereo-console 20261121 leaves nano's hash recorded and Debian's file at `/etc/nanorc.debian`; zsh-common, unpacked after the console, kept its file with both.
Machines that already lost a conffile this way are not repaired by this form; that is a repair of its own (reinstalling the owning package after the dpkg run).

## Removing a diversion in a successor, keeping the person's edit

Measured on 2026-11-21 with fixture packages (a conffile owner; a diverting package whose 1.0 puts a link or a plain file at the path and diverts the owning package's copy with `--rename`; a 2.0 that ships nothing there):

| 2.0 removes the diversion in | The owning package's file afterwards |
|---|---|
| its preinst (before dpkg unpacks 2.0) | **gone**: dpkg removes the path as a file of the old version that the new one no longer ships, and it is now the owning package's file (`dpkg -S` still names the owning package; `--verify` says MISSING) |
| its postinst (configure) | back at its name, a person's edit of it kept; nothing left at the diverted name; `--verify` clean, or `CHANGED` for the person's edit |

So the successor removes the diversion in its postinst: if the path is still its own link (or its own unchanged file), remove it, then `dpkg-divert --package NAME --remove --rename --divert DIVERTED PATH`.
Between the unpack and that postinst the path does not exist; a program that reads it in that window (a kernel's `update-grub` run by a package configured earlier in the same dpkg run) sees no file, so a successor whose file feeds a generated configuration runs the generator again at the end of its postinst.
A person's edit of the diverting package's own file at the path is not kept by this by itself: dpkg removes that file at the unpack, with no word, because it is no conffile (measured with sparky-stereo-console's former `/etc/skel/.bashrc`).
So the successor's preinst compares that file with the old version's `md5sums` (`dpkg-query --control-path`) and, when it differs, keeps a copy and says where in the ten languages (terminal and journal), as dpkg itself keeps a changed conffile beside a new one; the owning package's own file is then at the path.
Keep the copy outside a folder something copies whole: sparky-stereo-console keeps its former skel `.bashrc` as `/var/backups/sparky-stereo-console-skel.bashrc` (a trap below).

### The skel `.bashrc` moved to `.bash_aliases`, as built (sparky-stereo-console 20261121)

- Debian's skel `.bashrc` sources `~/.bash_aliases` after it has built the prompt and the `ls` alias, so `.bash_aliases` builds the prompt again the way `force_color_prompt=yes` would: colour only when `tput setaf 1` works (whatever `TERM` says), the plain prompt otherwise, then the xterm title prefix for `xterm*|rxvt*`.
  Setting only the coloured `PS1` there would give colour on a terminal where the published copy gave none.
- The proof is a new account's interactive shell before and after the upgrade: `PS1` (as `printf %q`), `alias`, `GCC_COLORS`, `EDITOR`, `VISUAL`, for `TERM` xterm-256color, linux and dumb, as a user, as root with the skel files, and as root with its own `/root/.bashrc` (base-files', which neither version touches): identical in all nine cases.
- `dpkg-stereo --verify`, the published 0.1.41 included, is clean on the untouched system after the upgrade: with no diversion of `.bashrc` there is nothing to misread.

## Traps

- **Symptom:** `dpkg-stereo --verify` says `CHANGED PATH (changed by the person)` on an untouched system, for a path one of our packages diverts.
  **Cause:** the verifier read the owning package's record at the path; fixed in dpkg-stereo 0.1.43.
  **How found:** the published edition installed as the round installs it; `dpkg-divert --list` beside `records/*.tsv`.
- **Symptom:** a conffile of the owning package is in `newconffile` state and its file is nowhere.
  **Cause:** above (the shared `.dpkg-new` name). **Fix:** do not divert a conffile; where a diversion stays, the safe form above. A package that makes its file at the path in its postinst instead of shipping it also keeps the owning package's file (fixtures), but the path is then no file of any package's list, so neither dpkg nor dpkg-stereo judges a person's edit of it.
- **Symptom:** after an upgrade, every new account made with `useradd -m` has a stray `.bashrc.dpkg-old` in its home.
  **Cause:** a copy kept in `/etc/skel`; useradd copies that folder whole (Debian's adduser skips `*.dpkg-old` by its `SKEL_IGNORE_REGEX`). **Fix:** keep such a copy outside `/etc/skel` (sparky-stereo-console uses `/var/backups`). **How found:** the proof's new account, listed before and after.
- **Symptom:** lintian `uses-dpkg-database-directly [preinst]`.
  **Cause:** reading the old version's `md5sums` from `/var/lib/dpkg/info`. **Fix:** `dpkg-query --control-path PACKAGE md5sums`.
- **Symptom:** the successor builds no `-lc-hr` companion where the published version had one.
  **Cause:** Lean Code projected the old `/etc/skel/.bashrc` (its shell handler knows the name) but does not classify `.bash_aliases` as shell, so the new file ships with its comments and needs no authored-text companion. Nothing breaks: the installed old companion depends on nothing.
  **How found:** the step 1 table of rows 629/802: the owning package's copy absent at the diverted name, then `dpkg-query ${Conffiles}` and `dpkg.log`.
- **Symptom:** after the upgrade that drops a diversion, the owning package's conffile is missing (`dpkg -S` names the owning package, `--verify` says MISSING), with no error from dpkg.
  **Cause:** the successor removed the diversion in its preinst; at the unpack dpkg removed the path as a file the old version shipped and the new one does not, and that was now the owning package's file.
  **Fix:** remove the diversion in the postinst. **How found:** fixture packages, both shapes (a link, a plain file), with and without a person's edit, both places (the table above).
