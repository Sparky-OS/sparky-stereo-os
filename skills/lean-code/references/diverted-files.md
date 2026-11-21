# A file under a dpkg diversion

**For whoever reads `dpkg-stereo --verify` on a system where a package diverts another package's file, or changes how dpkg-stereo reads a recorded file.**
Written on 2026-11-21 for dpkg-stereo 0.1.43 (queue rows 629 and 802), with dpkg 1.23.11+stereo3d3.

## Symptom

- On a system nobody touched, `dpkg-stereo --verify` exits 1 with `CHANGED   /etc/skel/.bashrc (changed by the person)`, or, after an upgrade to a package that diverts `/etc/grub.d/10_linux`, `CHANGED   /etc/grub.d/10_linux (changed by the person)`.
  The round's upgrade proof fails on that row (it is no planted edit).
- An edit of the owning package's copy under the diversion (`/etc/skel/.bashrc.debian`) is never reported.
- `--verify --deep` says `AFTERINST /usr/share/plymouth/plymouthd.defaults (changed after the install ...)` for an lc1 package's file that another package diverts.
- When the owning package of a diverted conffile is upgraded and the conffile changed, dpkg asks `Modified locally since installation`, exits 1 with no terminal and leaves `.dpkg-new`.

## Cause

dpkg keeps the diverting package's own copy at the path and every other package's copy at the diverted name.
dpkg-divert(1) of dpkg 1.23.11, `--package`: "package is the name of a package whose copy of file will not be diverted"; a `--local` diversion diverts every package's copy.
`/var/lib/dpkg/diversions` holds three lines per diversion: the path, the diverted name, and the diverting package or `:` for a local one.

Up to 0.1.42, dpkg-stereo read every record at its path (`P.real(path)`): in `--verify`, post-invoke, pre-invoke, `--restore` and `--repair`.
Its scan skipped a diverted path (both names), so a record made before the diversion was never refreshed, and none was made after.
A record of bash's `/etc/skel/.bashrc`, projected when dpkg-stereo was installed, was then read on sparky-stereo-console's file, which the console's preinst had put at that name with `dpkg-divert --rename` (bash's lean bytes moved to `.bashrc.debian`).

Only the conffiles whose owner was projected before the diversion existed show the row.
On the round's image bash is in the base container before dpkg-stereo, so its `.bashrc` has a record; `nano`, `zsh-common` and `initramfs-tools` arrive in the same apt run as the packages that divert their conffiles, so the scan met the diversion first and made no record; `/etc/issue`, `/etc/issue.net` and `10-uname` have no comments to remove and are never projected.
`grub2-common`'s `10_linux` was projected in the published image (boot 0.1.10 did not divert it) and diverted by the upgrade to 0.1.11.

## Fix (0.1.43)

- One helper says where dpkg keeps a package's copy (`on_disk(P, path, package)`): at the diverted name for every package but the diverting one.
  Every reader of a recorded file and every lc1 manifest row goes through it.
- The owning package's copy under another package's diversion is projected where dpkg keeps it, so its record follows its upgrades; the diverting package's own copy at the path is not projected (its lc1 manifest judges it), and a file at a diverted name is left alone.
- A line about a diverted file keeps the path as its first field (the round's proof parses it) and says where: `CHANGED   PATH (changed by the person, at NAME: OWNER's copy, diverted by OTHER)`.
- Beside it: a projected conffile that is the same in two versions of its package keeps its record under the new version (before, post-invoke deleted the old version's record and the scan found the lean bytes "already projected", so the next version that changed the file made dpkg ask about a file nobody touched).

## How it was found

- The published edition installed the way the round's case e installs it (the edition's dpkg and dpkg-stereo first, then the packages), untouched: `--verify` gave the `.bashrc` row and nothing else.
- `dpkg-divert --list`, `dpkg-query -S PATH` and `dpkg-query -W -f '${Conffiles}'` for each diverted path, and the `records/*.tsv` row of the path, side by side: only the paths with a record before the diversion appear.
- `grep -n 'P.real(' bin/dpkg-stereo` listed every reader.

## Test

`test/diversions-test.sh DPKG-STEREO.deb WORKDIR` in a throwaway container of the published edition, no network: ten scenarios (the untouched case, the edited replacement, the edited original, the owning package upgraded under the diversion with its conffile the same and then changed, restore, the diversion removed again, an edit kept through both, the diversion made before the owning package is installed, a conffile the same in two versions).
Red on 0.1.41 and 0.1.42 (24 passes, 18 failures), green on 0.1.43 (42 passes).
The fixture that diverts is an lc1 package sealed in the container with the installed toolkit: `PYTHONPATH=/usr/lib/dpkg-stereo python3 -c 'import sys; from lean import package; package.prepare(sys.argv[1], sys.argv[2])' TREE HR-DIR`; the HR folder must not exist yet ("HR staging directory must be new and separate").

## Traps

- **Symptom:** a fixture conffile is never projected (`left`: "the pointer line outweighs the comments it would replace").
  **Cause:** its comments are shorter than the pointer line. **Fix:** give a fixture two lines of real commentary.
- **Symptom:** after an upgrade, a person's edit is named `EDITED ... (changed by the person: left as they made it)` (not counted), where before the upgrade it was `CHANGED ...` (counted).
  **Cause:** on a new version the record goes and the scan leaves the edited file with that reason; this is the rule for every conffile, diverted or not, and the round's proof parses that exact line.

## 0.1.44: what the published edition left behind

Three repairs, each in the one engine, each proved by `test/repairs-test.sh` in the published-edition rig (red on 0.1.43 and 0.1.41).

- **A conffile a diversion kept from its package.** Symptom: `dpkg-query -W -f '${Conffiles}' nano` says `/etc/nanorc newconffile` and nothing is at `/etc/nanorc.debian` (also initramfs-tools' `update-initramfs.conf`).
  Cause: the diverting package's file at the path replaced the owning package's pending `PATH.dpkg-new` (edition-packaging, taking over a configuration file).
  Fix: when dpkg's diversions file changes, the post-invoke hook looks for such conffiles, writes `/var/lib/dpkg-stereo/diverted-conffiles.pending` and starts `dpkg-stereo-diverted-conffiles.service` with `--no-block`; the unit (`dpkg-stereo --repair-diverted`) waits for dpkg's locks (`apt-get check -o DPkg::Lock::Timeout=-1`) and reinstalls the owning packages at their installed version, so dpkg installs the conffile at the diverted name and records its hash.
  The packages whose .deb is in APT's cache go in one apt run with `--no-download`, the rest in another, downloaded only when the connection is not metered; never a question (`--force-confold`); what had to wait is kept as a problem with its size and the one command, and a timer retries hourly.
  It never runs inside dpkg-stereo's own lock: apt's dpkg run calls the hooks, which take that lock (the person's `--repair` runs it before taking it).
- **The records 0.1.41 and 0.1.42 lost.** Symptom: a lean conffile with a real hash, no record and no left row (`scripts/count-lost-records.py --list` in the lane counts them; 18 on a machine running 0.1.42).
  Fix: the migration `unrecorded-conffiles-v1` feeds them to the orphans' judgement (`orphan_plan`): the record comes back when the file is exactly the projection of its package's original at the installed version.
  The original comes first from dpkg-stereo's own pristine store, which keeps every conffile's original when it projects it, so on an installed machine nothing is usually downloaded; then APT's cache, then a configured source.
  Its remedies never say "the next upgrade gives them their record": for a conffile that upgrade is the question the record prevents.
- **Metered connections.** Nothing the hooks download by themselves (an original for a record, an owning package's .deb) is downloaded while NetworkManager's `Metered` is yes or guess-yes (read with `busctl`, as sparky-stereo-apt reads it); it is held, said, and fetched by a later dpkg run once the connection allows. The person's `--repair` downloads.
- **A person who is not root** gets `This needs root: sudo dpkg-stereo ARGS` and exit 2, not a traceback on the lock.

Traps met on the way:

- **Symptom:** the lost-record test is green with no cache and no network. **Cause:** the pristine store already held the originals. **Fix:** to prove the cache and source paths, remove the fixture's pristine copies (`/var/lib/dpkg-stereo/pristine/SHA256.xz` of the original) first. **How found:** the hook's own line "4 settings files have theirs back" in a run meant to hold.
- **Symptom:** in a container, the second package's reinstall fails with `E: Unable to fetch some archives` though its .deb was put in APT's cache. **Cause:** Debian's container images empty APT's cache after every `apt-get update` and every dpkg run apt makes (`/etc/apt/apt.conf.d/docker-clean`). **Fix:** one apt run for every cached package; in a test, put the .deb in the cache after the update. **How found:** `ls /var/cache/apt/archives` after the first reinstall.
- **Symptom:** a fixture conffile in an unknown folder (`/etc/NAME/NAME.conf`) gets no record. **Cause:** Lean Code classifies by consumer; an ini file in a folder no consumer reads is not projected. **Fix:** fixtures in the shapes of the real files (`/etc/default`, `/etc/systemd`).
