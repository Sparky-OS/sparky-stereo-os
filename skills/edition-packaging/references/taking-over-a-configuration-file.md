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
| `/etc/grub.d/10_linux` | grub2-common 2.14-5 | `/etc/grub.d/` takes scripts of our own; GRUB runs the last definition of a function, and `10_linux` calls `load_video` in each entry | the boot menu's own script redefines `load_video` (sparky-stereo-boot 0.1.13; system-housekeeping, boot-menu); the 0.1.12 diversion is removed in the postinst |

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
sparky-stereo-boot 0.1.13 carries the same form for initramfs-tools' `update-initramfs.conf`: with initramfs-tools 0.151 unpacked in one dpkg call and the boot package in a later one, the published 0.1.10 leaves `newconffile` and nothing at `update-initramfs.conf.debian`; 0.1.13 leaves initramfs-tools' hash recorded and Debian's file at `update-initramfs.conf.debian` with that hash (`.dpkg-new` moved by the preinst, measured on the real packages).
Machines that already lost a conffile this way are not repaired by this form: dpkg-stereo 0.1.44 does it, for any package's diversion, by reinstalling the owning package after the dpkg run (lean-code, [a file under a dpkg diversion](../../lean-code/references/diverted-files.md)).
An owning package's copy that sat at the diverted name when dpkg-stereo 0.1.41 or 0.1.42 lost its record (bash's skel `.bashrc` under the published console) gets the record back from dpkg-stereo 0.1.45, which judges a conffile where dpkg keeps it and again whenever dpkg's diversions change, so the copy keeps it when a successor gives the path back; one a person edited there is left as it is and named by `dpkg-stereo --verify` with its diverted name, where `dpkg --verify` gives no line.

## Our own file at a name we divert: made and kept by the maintainer scripts, never a conffile

Measured on 2026-11-22 (row 813) with dpkg 1.23.11+stereo3d3, fixture packages built from sparky-stereo-console's own maintainer-script templates (`tests/diverted-forms.sh` in its recipe), an owner with a conffile and a diverting package in two forms, each case in a fresh container, every apt run with no `--force-conf*` and stdin from `/dev/null`:

| Our file at the diverted name | The owning package installed first, then ours (the usual case: base-files is always there) | The owning package and ours in one run (apt, one dpkg call either order, two calls) | Upgrade from the plain file | Removal | Purge after removal |
|---|---|---|---|---|---|
| a conffile (C) | **asked**: our conffile takes the owning package's hash, our file is not installed, `end of file on <standard input> at conffile prompt`, rc 100 | installed | **asked**, as in the first column | **fails**: `dpkg-divert: error: rename involves overwriting '/etc/X' with different file '/etc/X.debian', not allowed`, package left half-installed | **the owning package's conffile is deleted** (`dpkg --verify`: `missing c /etc/X`) |
| made and kept by the postinst (S) | installed, the owning package's hash kept | installed, the owning package's hash kept, all four orders | untouched: the new default; changed: kept, the new default beside it, said once; nothing asked | the owning package's file back at its name; a changed file kept in `/var/backups/PACKAGE/PATH` and said | clean |

Why, in dpkg's own source (1.23.11):
- `src/main/unpack.c`, where a new conffile gets its old hash: "If several packages are listed as owning the file we pick one at random". The owning package lists the path too, so our new conffile can take the owning package's hash; at configure our file is absent (the preinst renamed the owning package's away) and `src/main/configure.c` then sees a file "Deleted locally since installation" and asks.
- `src/main/remove.c`: "Non-shared conffiles are kept" at `remove`, so our conffile stays at the path and `dpkg-divert --remove --rename` refuses to rename the owning package's copy over it (`src/divert/main.c`, `check_rename`).
- `src/main/remove.c`, purge: a conffile is dropped from the purge list only while another package's diversion covers it; `conffderef` follows the conffile's own name with no diversion lookup, so once our postrm has removed our diversion, purge unlinks the owning package's file.

So our file at a name we divert is not shipped in the package's data (Debian Policy 10.7.3 names this way: maintainer scripts that "create, update and maintain the file" and "must not overwrite the user's version").
The maintainer scripts keep it through ucf, Debian's tool for exactly this (ucf 3.0056, Priority standard, on the edition's image), so its records name what was written and `dpkg-stereo --verify` (0.1.46) names a file with other bytes (from 0.1.47 as differing from the default the package last offered, since ucf's record cannot tell who changed it: [lean-code](../../lean-code/references/diverted-files.md#why-the-row-does-not-say-changed-by-the-person)); a file of it that is gone is counted in the summary and never a problem, since ucf itself leaves a removed file removed ([lean-code, a file kept through ucf](../../lean-code/references/diverted-files.md#why-a-gone-file-is-no-fault)).

### Through ucf, with nothing asked (sparky-stereo-console 20261122, row 813)

Measured with fixture packages and ucf 3.0056 in the published-edition rig, every apt run `apt-get -y` with stdin from `/dev/null`, "at a terminal" meaning a pseudo-terminal (`script`) with debconf's readline frontend:

| The postinst calls | An untouched file, new default | A changed file, new default, at a terminal | The same with the round's `--force-confdef --force-confold` | A changed file under a running debconf frontend (`debconf-apt-progress`) |
|---|---|---|---|---|
| `ucf NEW PATH` | replaced, "Replacing config file PATH with new version" | **asked**: "What do you want to do about modified configuration file", the run waits | asked | **fails**: rc 100, the package half-configured |
| `UCF_FORCE_CONFFOLD=1 ucf NEW PATH` | **not replaced**: the old file stays, the new default goes to `PATH.ucf-dist`, and ucf records the new default's md5sum, so from then on the untouched file reads as changed | kept, `PATH.ucf-dist` | **asked**: dpkg passes `DPKG_FORCE=security-mac,downgrade,unsafe-io,confold,confdef`, and ucf's `confdef` unsets the choice | not measured |
| `DEBIAN_FRONTEND=noninteractive ucf NEW PATH` | replaced, the same line | kept, `PATH.ucf-dist`, nothing asked | kept, nothing asked | kept, nothing asked |

Why, in `/usr/bin/ucf` (3.0056): `DPKG_FORCE` "overrides all others" (`confdef` unsets the forced choice and stops reading the list); with no forced choice a changed file reaches the question `ucf/changeprompt` at priority critical, whose default is `keep_current`, and `keep_current` records the new default's md5sum and copies it to `PATH.ucf-dist`; debconf's noninteractive frontend takes that default without showing anything.
So the third form is ucf answering its own question with its own default: the person's file kept, the new default beside it.

As built in sparky-stereo-console 20261122 (Depends: `ucf (>= 3.0056)`):
- the defaults ship under `/usr/share/PACKAGE/defaults/PATH`;
- the postinst runs `DEBIAN_FRONTEND=noninteractive ucf --package PACKAGE DEFAULT PATH` and `ucfr PACKAGE PATH` for each file: ucf creates a missing one ("Creating config file PATH with new version"), replaces an untouched one, keeps one the person changed, replaced or removed and puts the new default beside it as `PATH.ucf-dist`;
- when `PATH.ucf-dist` was written anew, the package says once, in ten languages, on the terminal and in the journal, that the person's file is kept and where the new default is (ucf's own English lines go only to the terminal and `/var/log/apt/term.log`);
- ucf copies a default it creates with the default's mode, so a script in `/etc/update-motd.d` gets `chmod 755` when ucf created it, and the default beside a kept one stays 644;
- the upgrade from the plain files: the preinst sets each old file aside and marks it changed when it is not the old version's bytes (`dpkg-query --control-path PACKAGE md5sums`); the postinst drops an untouched one, so ucf creates the new default, and puts a changed one back first, so ucf, which has no record of it, keeps it with the new default beside it;
- the postrm, at removal, deletes a file whose md5sum is the one ucf recorded (read from `/var/lib/ucf/hashfile`: Policy 6.5 lets a postrm rely only on Essential packages), keeps a changed one in `/var/backups/PACKAGE/PATH` (said), runs `ucf --package PACKAGE --purge PATH` and `ucfr --purge PACKAGE PATH`, and only then removes the diversion with `--rename`;
- the safe form F2 above stays in the preinst for the owning package's pending `.dpkg-new`;
- the package ships every folder it puts a file into, empty if need be (`/etc/zsh` and `/etc/update-motd.d` from 20261122.1), so dpkg never removes one under the files ucf keeps there (a trap below); the postrm removes such a folder at the removal when it is left empty and no other package lists it (`dpkg-query -S`), and the folders it made under `/var/backups/PACKAGE` at the purge when nothing of the person's is in them; the postinst removes `/var/lib/PACKAGE` when its scratch is emptied.

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
Measured with sparky-stereo-boot 0.1.13, both ways it reaches machines: from 0.1.12 (which diverted `10_linux`) the diversion goes in the postinst and grub2-common's file is back, a person's edit of it kept and named at its own path; from the published 0.1.10 (which never diverted it) there is nothing to give back, and a person's edit of grub2-common's `10_linux` and of the package's own `update-initramfs.conf.sparky-stereo` are kept through the upgrade and the removal; `dpkg-stereo --verify` is clean on the untouched system before, after and after the removal; the postinst's `update-grub` wrote the new menu at the upgrade, seen at boot.
Keep the copy outside a folder something copies whole: sparky-stereo-console keeps its former skel `.bashrc` as `/var/backups/sparky-stereo-console-skel.bashrc` (a trap below).

### The skel `.bashrc` moved to `.bash_aliases`, as built (sparky-stereo-console 20261121)

- Debian's skel `.bashrc` sources `~/.bash_aliases` after it has built the prompt and the `ls` alias, so `.bash_aliases` builds the prompt again the way `force_color_prompt=yes` would: colour only when `tput setaf 1` works (whatever `TERM` says), the plain prompt otherwise, then the xterm title prefix for `xterm*|rxvt*`.
  Setting only the coloured `PS1` there would give colour on a terminal where the published copy gave none.
- The proof is a new account's interactive shell before and after the upgrade: `PS1` (as `printf %q`), `alias`, `GCC_COLORS`, `EDITOR`, `VISUAL`, for `TERM` xterm-256color, linux and dumb, as a user, as root with the skel files, and as root with its own `/root/.bashrc` (base-files', which neither version touches): identical in all nine cases.
- `dpkg-stereo --verify`, the published 0.1.41 included, is clean on the untouched system after the upgrade: with no diversion of `.bashrc` there is nothing to misread.
- A file in `/etc/skel` lands in every new account's home, so its comments say only what its lines do; a quote of a request or a design note goes in the recipe's comment. From 20261121.1 the file ships lean (Lean Code 0.1.31: the pointer line and the code), and its authored text is in `sparky-stereo-console-lc-hr`, as the skel `.bashrc`'s was up to 20261102.

## Traps

- **Symptom:** on a machine without zsh-common the upgrade stops: `Creating config file /etc/zsh/zshrc with new version`, `cp: cannot create regular file '/etc/zsh/zshrc': No such file or directory`, `dpkg: error processing package sparky-stereo-console (--configure)`, apt exit 100; a fresh install stops the same way.
  **Cause:** a folder only we owned leaves with our plain file. The published console shipped `/etc/zsh/zshrc` as a plain file and, without zsh-common, was the only package listing `/etc/zsh`; 20261122 shipped nothing in that folder, so at the unpack dpkg removed the file and the empty folder, and ucf creates no parent folder.
  **Fix:** the package ships every folder it puts a file into (sparky-stereo-console 20261122.1). dpkg-maintscript-helper(1) gives the same rule for the folders of its symlink and directory switches: they "need to be shipped in the new packages, or dpkg will not be able to remove them on purge". Measured against the other form, the postinst making the folder before ucf: it configures too, but the folder is in no package's list (`dpkg -S` finds nothing) and zsh-common's purge then warns `directory '/etc/zsh' not empty so not removed`.
  **How found:** on an installed machine, not in the rig. The rig installed every owning package together with the packages that divert their files, so zsh-common was always there; a minimal edition rig (the round's sources, the edition's dpkg and dpkg-stereo, ucf and the published console with no recommends) showed `dpkg -S /etc/zsh` naming the console alone, and reproduced the stop. Read `dpkg -S` of the parent of every file the scripts keep, on the smallest system the package installs on.
- **Symptom:** after the upgrade an empty `/var/lib/sparky-stereo-console` stays, and after the purge an empty `/var/backups/sparky-stereo-console/etc/skel`.
  **Cause:** the scripts removed the files they kept there, and not the folders they had made for them.
  **Fix:** remove each such folder when it is left empty and no other package lists it (above). **How found:** the console's test lists every empty folder of ours that no other package lists, after the upgrade, the removal and the purge.
- **Symptom:** after the owning package is purged while ours still diverts its conffile, its file stays at the diverted name (`/etc/zsh/zshrc.debian`, zsh-common's own bytes), and our later removal gives it back at the name, a file of no installed package.
  **Cause:** dpkg's purge drops a conffile from its list while another package's diversion covers it (`src/main/remove.c`, above): Policy's "dpkg does not handle it well".
  **Not changed:** our file and ucf's record of it are untouched throughout; the leftover is the owning package's, and is listed for the main session. **How found:** the console's test case `zsh-later` (zsh-common installed after the console and purged again).

- **Symptom:** `dpkg-stereo --verify` says `CHANGED PATH (changed by the person)` on an untouched system, for a path one of our packages diverts.
  **Cause:** the verifier read the owning package's record at the path; fixed in dpkg-stereo 0.1.43.
  **How found:** the published edition installed as the round installs it; `dpkg-divert --list` beside `records/*.tsv`.
- **Symptom:** a conffile of the owning package is in `newconffile` state and its file is nowhere.
  **Cause:** above (the shared `.dpkg-new` name). **Fix:** do not divert a conffile; where a diversion stays, the safe form above. A package that makes its file at the path in its postinst instead of shipping it also keeps the owning package's file (fixtures); the path is then no file of any package's list, so it keeps it through ucf, whose records `dpkg-stereo --verify` reads from 0.1.46 (above).
- **Symptom:** after an upgrade, every new account made with `useradd -m` has a stray `.bashrc.dpkg-old` in its home.
  **Cause:** a copy kept in `/etc/skel`; useradd copies that folder whole (Debian's adduser skips `*.dpkg-old` by its `SKEL_IGNORE_REGEX`). **Fix:** keep such a copy outside `/etc/skel` (sparky-stereo-console uses `/var/backups`). **How found:** the proof's new account, listed before and after.
- **Symptom:** lintian `uses-dpkg-database-directly [preinst]`.
  **Cause:** reading the old version's `md5sums` from `/var/lib/dpkg/info`. **Fix:** `dpkg-query --control-path PACKAGE md5sums`.
- **Symptom:** the successor builds no `-lc-hr` companion where the published version had one.
  **Cause:** up to Lean Code 0.1.30 the shell handler knew `.bashrc` by name but not `.bash_aliases`, so the new file shipped with its comments and needed no authored-text companion, and a machine kept the old companion with nobody's text in it.
  **Fix:** Lean Code 0.1.31 classifies bash's startup files by name (`.bashrc`, `.bash_aliases`, `.bash_logout`, `.bash_profile`, `.bash_login`, `.profile`); rebuild the package with it (sparky-stereo-console 20261121.1).
  **How found:** `dpkg-deb -c` of the successor beside the published pair: the companion was missing from the build output.
- **Symptom:** a standalone recipe's `lean.release check-debs` stops with `matching HR documentation package is missing` after a rebuild that starts to project a file.
  **Cause:** the recipe passed only `./PKG_VERSION_all.deb`; once a file is projected the package's manifest names its `-lc-hr` companion, and `check-debs` requires the pair together.
  **Fix:** pass both, `./"$PKG"*_"$VERSION"_all.deb` (sparky-stereo-console's recipe; dpkg-stereo's passes `./*.deb` into an output folder of its own).
  **How found:** `lean/release.py` `check_debs()`, read before the first build with 0.1.31.
- **Symptom:** at the upgrade that removes a diversion, dpkg prints `warning: cannot delete old directory '/etc/sparky-stereo-boot': Directory not empty`.
  **Cause:** the old version shipped the folder that holds the diverted name; at the unpack dpkg tries to remove it, while the owning package's diverted copy is still in it until the postinst renames it back.
  **Effect:** none: the postinst renames the copy back and removes the empty folder (`rmdir`), `dpkg --audit` is clean. Shipping the folder again would leave it empty and owned for good.
  **How found:** the upgrade rows of sparky-stereo-boot 0.1.12 to 0.1.13 (rows 629/802), dpkg's own output.
- **Symptom:** a person's edit of the program the diversion pointed at (`/usr/lib/...`) is gone after the upgrade that removes the diversion, with no word.
  **Cause:** dpkg removes a file the new version no longer ships; under `/usr` no edit survives any upgrade (Policy 10.7.2: configuration files reside in `/etc`). Measured with sparky-stereo-boot 0.1.12's `10_linux` program; dpkg-stereo had called it `LCCHANGED` before.
- **Symptom:** after the upgrade that drops a diversion, the owning package's conffile is missing (`dpkg -S` names the owning package, `--verify` says MISSING), with no error from dpkg.
  **Cause:** the successor removed the diversion in its preinst; at the unpack dpkg removed the path as a file the old version shipped and the new one does not, and that was now the owning package's file.
  **Fix:** remove the diversion in the postinst. **How found:** fixture packages, both shapes (a link, a plain file), with and without a person's edit, both places (the table above).
- **Symptom:** installing our package on a system where the owning package is already installed stops with `Configuration file '/etc/X' ==> Deleted locally since installation.` and `end of file on <standard input> at conffile prompt` (rc 100, our package left unpacked), though nobody touched anything.
  **Cause:** our package lists `/etc/X`, a name it diverts, in `DEBIAN/conffiles`; dpkg gave our new conffile the owning package's hash (unpack.c: "we pick one at random"). **Fix:** never list a diverted name as our conffile; make and keep the file in the maintainer scripts (the section above). **How found:** the fixture order "the owning package first", `dpkg-query -W -f '${Conffiles}'` of our package showing the owning package's md5 for `/etc/X`.
- **Symptom:** a fixture case fails in a way the case alone cannot explain (the owning package's conffile with our hash, a question at the owning package's configure).
  **Cause:** an earlier case in the same container left a package in `config-files` state that still lists the shared path as its conffile, and the next install inherited that hash (the same "at random" choice). **Fix:** one fresh container per case. **How found:** the same case passed alone.
- **Symptom:** `apt-get update` with a flat `file:` source says `Symlinking file  to /var/lib/apt/lists/partial/..._Packages.zst failed` and the packages are not found. **Fix:** give apt the `.deb` files by path (`apt-get install ./a.deb ./b.deb`); apt still orders and splits the dpkg calls itself.
- **Symptom:** after the install, the owning package's copy at the diverted name (`/etc/issue.debian`) holds our default, ucf's hashfile lists the diverted name, and the file at the name is missing or not ours.
  **Cause:** ucf follows a dpkg diversion unless the caller is the diverting package: `ucf --help`, "-P foo, --package foo   Don't follow dpkg-divert diversions by package foo" (`/usr/bin/ucf` 399-407 runs `dpkg-divert --truename`).
  **Fix:** `ucf --package PACKAGE DEFAULT PATH`, and `ucf --package PACKAGE --purge PATH` at removal. **How found:** the console's `tests/etc-files.sh` fresh and up-none ("is the package's" failed for all five), then a fixture's `ls /etc/default/uc-demo*`.
- **Symptom:** after a removal and a new install, a file the package keeps through ucf is not there, and ucf printed "Not replacing deleted config file".
  **Cause:** ucf's record outlived the file: when its md5sum is the new default's and the file is gone, ucf takes the person's removal as kept (`/usr/bin/ucf` 811-821). A diverting package's file leaves its name at the removal, so the owning package's file can come back.
  **Fix:** purge the package's ucf records at `remove`, not only at `purge`. **How found:** `/usr/bin/ucf`'s own source, then the console's reinstall row.
- **Symptom:** `UCF_FORCE_CONFFOLD=1` leaves an untouched file at the old default, with `PATH.ucf-dist` beside it, and the next verify calls it changed.
  **Cause:** ucf's "keep the old file" covers an unmodified file too (`/usr/bin/ucf` 863-872), unlike dpkg's `--force-confold`, and it records the new default's md5sum. **Fix:** the noninteractive form above. **How found:** the fixture row `old:untouched`.
- **Symptom:** a fixture's purge deletes the owning package's file that its removal had just given back.
  **Cause:** dpkg calls the postrm with `remove` and then with `purge`; a block run for both, after the diversion is gone, removes the owning package's file at the name. **Fix:** act only while `dpkg-divert --listpackage PATH` names the package itself (the console's postrm does). **How found:** dpkg-stereo's `test/ucf-test.sh` U7.
