# A file under a dpkg diversion

**For whoever reads `dpkg-stereo --verify` on a system where a package diverts another package's file, or changes how dpkg-stereo reads a recorded file.**
Written on 2026-11-21 for dpkg-stereo 0.1.43 (queue rows 629 and 802), with dpkg 1.23.11+stereo3d3; extended for 0.1.44 to 0.1.47 (2026-11-22).

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

### Why the repair may pass `--force-confdef` and `--force-confold`, and an uplift by hand may not

The repair reinstalls a package at the version that is installed, from that version's own .deb, so no conffile of the package changes.
dpkg(1) of dpkg 1.23.11 gives each of the three flags a say only in that other case: `confold` "If a conffile has been modified and the version in the package did change, always keep the old version without prompting", `confnew` the same with "always install the new version", and `confdef` "If a conffile has been modified and the version in the package did change, always choose the default action without prompting".
With the package's version of every conffile unchanged, dpkg keeps each file on the disk as it is, edited or not, and the flags decide nothing; they are there so that an unattended run never stops at a question if a .deb of the same version should carry another conffile, and then the person's file is the one kept.
`test/repairs-test.sh` shows it: initramfs-tools, reinstalled by the repair, has two more conffiles, one edited by the person and one whose record was lost; after the repair both are byte for byte as they were, nothing waits beside them (`.dpkg-dist`, `.dpkg-new`, `.dpkg-old`), and `--verify` names only the edited one.
The rule against these flags in an uplift by hand stands: there the package's conffiles do change, and with them dpkg keeps every old file without a word and writes the new one as `.dpkg-dist` ([edition-packaging, the formula](../../edition-packaging/references/sparky-formula.md#files-under-etc-are-conffiles)), so a machine would keep a stale file for good and nobody would be asked.
`confmiss` is never passed: it "means not preserving a change (removing) made to the file".

Traps met on the way:

- **Symptom:** the lost-record test is green with no cache and no network. **Cause:** the pristine store already held the originals. **Fix:** to prove the cache and source paths, remove the fixture's pristine copies (`/var/lib/dpkg-stereo/pristine/SHA256.xz` of the original) first. **How found:** the hook's own line "4 settings files have theirs back" in a run meant to hold.
- **Symptom:** in a container, the second package's reinstall fails with `E: Unable to fetch some archives` though its .deb was put in APT's cache. **Cause:** Debian's container images empty APT's cache after every `apt-get update` and every dpkg run apt makes (`/etc/apt/apt.conf.d/docker-clean`). **Fix:** one apt run for every cached package; in a test, put the .deb in the cache after the update. **How found:** `ls /var/cache/apt/archives` after the first reinstall.
- **Symptom:** a fixture conffile in an unknown folder (`/etc/NAME/NAME.conf`) gets no record. **Cause:** Lean Code classifies by consumer; an ini file in a folder no consumer reads is not projected. **Fix:** fixtures in the shapes of the real files (`/etc/default`, `/etc/systemd`).
- **Symptom:** `test/modes-test.sh` on the published edition with no network fails 7 rows with 0.1.44 (`S0 no conffile problem kept`, `S2 repair exits 0 (1)`, ...), and passes with the network.
  **Cause:** from 0.1.44 every `--repair` also installs the conffiles the published edition lost (nano's, initramfs-tools'), and with no network and no .deb it keeps its `diverted` problem, which is right.
  **Fix:** run it as `modes-test.sh DEB WORKDIR DEBS`, DEBS a folder with those packages' .deb files at their installed versions: they go into APT's cache, the first repair installs the conffiles offline, and a row says so (28 rows pass). **How found:** the failing rows' problem list named `diverted`, not the folders.
- **Symptom:** after the repair reinstalled a package, `--verify` prints `EDITED    PATH (changed by the person: left as they made it)` (not counted) for a lean conffile nobody touched; before the reinstall it printed nothing for it.
  **Cause:** the file's record was lost after 0.1.44's one-time migration had run (the test removes it by hand); apt runs `dpkg --unpack` and `dpkg --configure` as two dpkg runs, the first one's post-invoke leaves the unpacked package out of `packages.tsv`, so the configure run's post-invoke takes it for a changed package and projects it whole, and that scan, finding lean bytes that differ from dpkg's hash and no record, left the file as the person's. The bytes stay as they were, and 0.1.44's `--repair` did not give the record back, because the migration looked only at files without a left row.
  **Fixed in 0.1.45:** the scan hands such a file (a conffile, no record of this version, the Lean Code pointer, other bytes than dpkg's hash) to the one judgement instead of calling it the person's; the record comes back from the pristine store, and the judgement also takes a left row that calls a lean file the person's, so a machine where 0.1.44 wrote the untrue row is corrected at the install of 0.1.45 or in `--repair`. `test/repairs-test.sh` part 3 has the row (red on 0.1.44).
  **How found:** `--verify` read before and after a same-version reinstall of initramfs-tools from APT's cache, with one record removed; then a stack print at the one writer of that left row, `Records.__setitem__` for kind `left`, in a throwaway container: `post_invoke` (the configure run) → `project_packages(full)` → `PERSON_CHANGED`.
- **Symptom:** after the round's upgrade (dpkg-stereo 0.1.44, the console 20261121.1) on a published system whose bash had an update while the console diverted `/etc/skel/.bashrc`, bash's `/etc/skel/.bashrc` is lean and has no record; `--verify` is clean, `--repair` does not change it, and a person's edit of it is named by nobody but `dpkg --verify`.
  **Cause:** bash's update under 0.1.41 dropped the records of its four skel and bashrc files (`count-lost-records.py --list`: 5 lean conffiles without a record, one of them `(at /etc/skel/.bashrc.debian)`); 0.1.44's one-time migration, in the dpkg run of the upgrade, gave back 4 ("4 settings files have theirs back") but not the copy at the diverted name, and the console's postinst then moved that copy to `/etc/skel/.bashrc`.
  **Fixed in 0.1.45:** the judgement reads a conffile where dpkg keeps it (`on_disk`) and leaves out only the diverting package's own copy and a local diversion (`diverted_away`), so the copy at `.bashrc.debian` gets its record back at the install of 0.1.45, and keeps it when the console gives the path back; it also runs again whenever dpkg's diversions change, so a copy that loses its record later is caught in the run that moves it. `test/repairs-test.sh` part 4 has the rows (red on 0.1.44, where the next changed version made dpkg ask); the lane's round-style rig counts 0 lean conffiles without a record after the upgrade.
  **How found:** `count-lost-records.py --list` before the upgrade, after it and after `--repair`, on the published rig brought up to date with its own lists.

## 0.1.45: one judgement for a lean conffile without a record, where dpkg keeps it

**Symptom:** after the round's upgrade, bash's `/etc/skel/.bashrc` is lean with no record and `--verify` is clean (previous trap); after `apt-get install --reinstall PACKAGE`, `--verify` says `EDITED    PATH (changed by the person: left as they made it)` for a lean conffile nobody touched; a person's edit of zsh-common's `/etc/zsh/zshrc.debian` or base-files' `/etc/issue.debian` is named by nothing (`dpkg --verify` gives no line at a diverted name either).

**Fix:** the judgement of a lean conffile without a record (`orphan_plan`, through `migrate_orphans` kind `unrecorded`) is the one place that decides such a file:
- it reads the copy where dpkg keeps it (`on_disk`), leaving out only the diverting package's own copy and a local diversion (`diverted_away`);
- it runs once after the install of 0.1.45 (marker `unrecorded-conffiles-v2`, which replaces 0.1.44's v1 and its state files), in the person's `--repair` and `--repair-consumers`, and whenever a dpkg run changed `/var/lib/dpkg/diversions` (the stamp the diverted-conffile repair already keeps); and the projection of a package a dpkg run unpacked hands it each lean conffile it finds without a record, when that file's original is in the pristine store;
- exactly the projection of its package's file: the record comes back; anything else: the person's, left byte for byte, with a left row so `--verify` names it;
- an owner's copy at a diverted name that no projection ever judged (`unprojected_diverted`: no record, no left row) goes through the projection, which records it when it is its package's file and names it when it is not;
- `--verify` names an lc1 package's conffile at a diverted name that differs from its payload, without `--deep` too;
- an EDITED line about a diverted copy says where it is, in its own parentheses before the fixed end the round's upgrade proof matches: `EDITED    /etc/zsh/zshrc (at /etc/zsh/zshrc.debian: zsh-common's copy, diverted by sparky-stereo-console) (changed by the person: left as they made it)`.

**Why the projection hands over only with the original at hand:** the engine keeps the original of every conffile it projected (`/var/lib/dpkg-stereo/pristine`, never pruned). With the original of dpkg's hash there, the judgement can say whether the file is its projection, which is every untrue case measured (a same-version reinstall; a copy under a diversion). Without it, the file is not the projection of anything this engine projected at that version: an upgrade changed the conffile and the old lean file was kept by the person's answer or `--force-confold`, which dpkg keeps as a local change too; it stays the person's, as before, and nothing is fetched to say so.
The first build handed over every such file; `test/diversions-test.sh` scenario 8 (a person's edit, then an upgrade that changed the conffile, kept with `--force-confold`) then found nothing named: the original of the new version was nowhere, the judgement waited, and the edit went unnamed.

**What it costs, with nothing to do** (the published edition brought up to date, 0.1.45 installed, median of five runs in a container): the judgement over every package 157 to 180 ms; `dpkg-stereo --repair` 214 to 218 ms; a post-invoke hook after dpkg's diversions changed 189 to 211 ms (0.1.44: 33 ms); a post-invoke hook with nothing changed 19 to 21 ms (0.1.44: 32 ms: the projection's hand-over costs nothing when it finds nothing). Measure `--repair` only after the diverted-conffile repair has nothing left: on a rig where nano's and initramfs-tools' conffiles are still lost, its apt run fails offline and takes 12 s, in 0.1.44 too.
An owner's copy at a diverted name that Lean Code cannot project (zsh-common's `/etc/zsh/zshrc`: "no qualified adapter for this consumer") gets no record and stays its package's file; each judgement looks at it again, which is part of the time above.

**Test:** `test/repairs-test.sh` part 3's last row and part 4, in the published-edition rig with no network: the lost record under a diversion back, kept when the diversion goes in a later dpkg run, the next changed version asking nothing; an unprojected copy at a diverted name recorded, or named and kept byte for byte; a record lost later back in the dpkg run that changes the diversions and in `--repair`; the reinstall without the untrue EDITED.
Green on 0.1.45: 28 passes; red on 0.1.44: exactly the 9 new rows fail (one of them dpkg asking `Configuration file ... Modified locally` at the next changed version); 0.1.43: 19 failures; 0.1.41: 20.
`test/diversions-test.sh` scenario 8 expects the diverted copy's EDITED line with its diverted name: 42 passes on 0.1.45, that one row red on 0.1.44.

Traps met on the way:

- **Symptom:** a patch of `/usr/sbin/dpkg-stereo` in a container changes nothing. **Cause:** that file only loads `/usr/lib/dpkg-stereo/dpkg_stereo.py`, whose byte-compiled form Python reads. **Fix:** patch the module and compile it again (`py_compile.compile(p, cfile=importlib.util.cache_from_source(p))`). **How found:** the first trace run printed no stack.
- **Symptom:** a test's "lost record" behaves unlike a real one. **Cause:** dpkg-stereo keeps a conffile's record twice: in `records/PACKAGE.tsv` and in the conffile index `conffiles.tsv` that pre-invoke and dpkg's own check read; a row removed from the first only is still known to them. **Fix:** remove both, as 0.1.41 and 0.1.42 lost them (`forget` in `repairs-test.sh`).
- **Symptom:** a check that `--verify` exits 0 fails in a test that also planted a person's edit. **Cause:** `CHANGED` for an edited projected conffile is counted, `EDITED` is not. **Fix:** check the rows, not the exit status, when an edit is planted.

## A file kept through ucf (row 813, dpkg-stereo 0.1.46)

**Symptom:** a person's change to a file that maintainer scripts keep (sparky-stereo-console's `/etc/issue`, `issue.net`, `nanorc`, `zsh/zshrc`, `update-motd.d/10-uname` at the names it diverts; samba-common's `/etc/samba/smb.conf`; grub's `/etc/default/grub`) is kept, and `dpkg-stereo --verify` up to 0.1.45, `--verify --deep` and `dpkg --verify` all give no line for it.
**Cause:** such a file is in no package's file list, and the verifier judged only listed files.
**Fix (0.1.46):** `--verify` reads ucf's records, read only: the md5sum of what ucf last wrote (`/var/lib/ucf/hashfile`, "md5  path") and the package `ucfr` registered (`/var/lib/ucf/registry`).
- other bytes (0.1.47): `EDITED    PATH (kept by PACKAGE through ucf) (differs from the default PACKAGE last offered: left as it is)`, not counted; with `, which is beside it as PATH.ucf-dist` before the colon when that file holds the default ucf recorded; `(kept through ucf) (differs from the default last offered: left as it is)` when no package registered it (nfs-common hands `/etc/nfs.conf` and `/etc/idmapd.conf` to ucf without `ucfr`); the sentence is LOCAL103 to LOCAL106, in the ten languages ([why not "changed by the person"](#why-the-row-does-not-say-changed-by-the-person)); 0.1.46 printed `(changed by the person: left as they made it)` there;
- a file that is gone: no row, not counted, and the exit status is not changed by it; the summary line says `N files kept through ucf are gone (ucf leaves a removed file removed)` (LOCAL102, ten languages) when N is not 0, and `--verify --deep` lists each as `GONE      PATH (kept by PACKAGE through ucf)`, also not counted ([why](#why-a-gone-file-is-no-fault)); a link whose target is gone is no gone file: it stands at the name and is `EDITED`;
- a path a package lists as its own conffile, where that package's copy is, stays with that package's judgement; under a diversion the owning package's record keeps the path's name while its copy is at the diverted name, so the file at the name (the diverting package's, kept through ucf) is judged by ucf's record;
- a non-root `--verify` stops at the existing `This needs root: sudo dpkg-stereo --verify` before it reads anything; a file root cannot read is counted in the summary and said once, and the check is then incomplete (exit 2);
- the dpkg hooks never read `/var/lib/ucf` (a Python audit hook logged no open there across a `dpkg -i` and a `dpkg -P`), and nothing there is written.
**How found:** the console's `tests/etc-files.sh up-edited` and the lane's round-style mode `console8` (each change kept and said, no row); then ucf's records read on a long-used edition machine and in the rig.
**Test:** `test/ucf-test.sh DEB WORKDIR` in the published-edition rig with ucf, samba-common, nfs-common and grub-efi-amd64 installed: 55 passes on 0.1.47; on 0.1.46, 21 rows fail: every ucf row in the new wording and all of U11 (the three measured shapes, a `.ucf-dist` that is not the recorded default, the sentence in each of the ten languages). With 0.1.46's version of the test: 38 passes on 0.1.46; on the first build of 0.1.46, which printed a gone file as `MISSING` and counted it, exactly the ten rows of U4 fail; on 0.1.45, which reads no ucf record, twelve.
U4 removes samba-common's registered `smb.conf` by hand and installs a fixture whose second version's postinst removes its own ucf-kept file with `rm -f` and no `ucf --purge` (libdebuginfod-common's shape), then a link with a missing target at an unregistered name.
The lane's round-style proof does the same at the edition's scale: on the published edition with ucf, samba-common's `smb.conf` removed before the upgrade, then the real `dist-upgrade`; after it `--verify` exits 0 with no row for the file and one gone file in its summary, and `--deep` lists it as `GONE` and exits 0.

### Why the row does not say "changed by the person"

- **What ucf records.** `/var/lib/ucf/hashfile` holds the md5sum of the default the package last handed to ucf, not of anything a person did; a file whose bytes differ from it was changed after ucf wrote it, by someone or something the record does not name.
- **Measured on 2026-11-22 on an installed edition machine nobody had edited these files on** (dpkg-stereo 0.1.46 printed all three as `changed by the person`):
  - `/etc/libreoffice/registry/main.xcd`: libreoffice-common's own older default, kept by ucf at an upgrade, with the new default beside it as `main.xcd.ucf-dist` (four lines differ: the version strings);
  - `/etc/R/Renviron`: r-base-core's postinst writes the paper size into it after ucf;
  - `/etc/default/grub`: the menu settings written at installation.
- **So the row says only what the records show** (the main session's ruling for continuation 14): the file differs from the default the package last offered, and is left as it is; when `PATH.ucf-dist` holds that default, the row names it, since that is where the person finds it. A `.ucf-dist` with other bytes is not named as it.
- **What does not change:** the keyword `EDITED`, the counting (never a problem) and the exit status.
- **The round's own parser:** case e's `check_verify` passes any run that exits 0, and in a run that exits 1 (planted edits) lets an `EDITED` row through only with the fixed end `(changed by the person: left as they made it)` and a planted path; a ucf row in the new wording there is called a problem. The round's image had no ucf-kept file with other bytes when this was written; the lane's round-style modes `ucf2` and `owners` match the new wording.
- **Not changed yet:** the sentence for dpkg's own conffiles keeps `(changed by the person ...)`, with the same doubt (dpkg's record is the hash of the conffile it installed, and a package's own script can change a conffile too, though Policy 10.7.4 says "The maintainer scripts must not alter a conffile of any package, including the one the scripts belong to").

### Why a gone file is no fault

- **ucf's own meaning.** `/usr/bin/ucf` (3.0056, lines 811-821): when a file is gone and the new default is the one ucf last wrote, it says "Not replacing deleted config file" and leaves it gone; only `UCF_FORCE_CONFFMISS` brings it back. To ucf a removed file is somebody's decision, not damage.
- **Who removed it cannot be told.** A person, ucf's own choice, or a package's script that removed the file without telling ucf (next trap): the records look the same in every case. So the file is neither a fault nor "changed by the person".
- **A problem row nobody can act on is an untrue alarm.** Measured on 2026-11-22 on two edition machines in daily use that nobody touched that way: ucf's records named `/etc/profile.d/debuginfod.sh` and `.csh`, both gone, on both machines, and `/etc/cron.d/geoip-database-contrib` as well on the second (35 records there). The first 0.1.46 build would have made `--verify` report two and three problems there and exit 1.
- **What stays judged.** Anything that stands at the name: other bytes, a file of another kind, a link (even one whose target is gone) is `EDITED`. A path a package also lists as its own conffile stays with that package's record: a projected conffile that is gone is still `MISSING` and counted, as before.

Traps:
- **Symptom:** `dpkg-stereo --verify` 0.1.46 says `EDITED    /etc/R/Renviron (kept by r-base-core through ucf) (changed by the person: left as they made it)`, and the same for `/etc/default/grub` and libreoffice-common's `main.xcd`, on a machine where nobody edited them.
  **Cause:** ucf's record is the default the package last offered; a package's own script (r-base-core's postinst) and ucf's own "keep the old file" (libreoffice-common's main.xcd, with `main.xcd.ucf-dist` beside it) leave other bytes than the record as well as a person does.
  **Fix (0.1.47):** the row says that the file differs from the default the package last offered, and names `PATH.ucf-dist` when it holds that default ([above](#why-the-row-does-not-say-changed-by-the-person)).
  **How found:** on an installed edition machine, not in the rig: the rig's ucf-kept files were all untouched; each row's file compared with ucf's record and with its `.ucf-dist`, and the package's postinst read.
- **Symptom:** on a system nobody touched, a ucf-kept file differs from ucf's md5sum: `/etc/default/nfs-common`, whose first line is the Lean Code pointer while ucf's cached copy (`/var/lib/ucf/cache/:etc:default:nfs-common`) has the comments.
  **Cause:** nfs-common lists the file as its conffile and also hands it to `ucf --three-way`; Lean Code projects it as a conffile (its record's original md5sum is ucf's), so ucf's md5sum is of the original. **Fix:** the verifier leaves a path a package lists as its conffile to that package's record. **How found:** each hashfile row's md5sum against the file on the untouched rig; a long-used edition machine shows the same file the same way.
  **Not proven:** what ucf does at nfs-common's next upgrade that changes that default: it compares the lean file with the original's md5sum, and it would take the projection for a person's change unless dpkg-stereo's pre-invoke gives the original back first.
- **Symptom:** with the first build of 0.1.46, `--verify` says `MISSING   /etc/profile.d/debuginfod.sh (kept by libdebuginfod-common through ucf)` (and `.csh`) and exits 1 on a machine nobody touched.
  **Cause:** ucf's records outlive files that are gone. libdebuginfod-common 0.196-1's postinst runs `rm -f /etc/profile.d/debuginfod.sh` (and `.csh`) when its debconf answer `libdebuginfod/usedebiandebuginfod` is false, with no `ucf --purge` and no `ucfr --purge`; its postrm at purge skips ucf's records when the file is already gone (`[ -f FILE ] || continue`), so they can outlive the package too. Both scripts act only where `/etc/os-release` says `ID=debian` or `ID=ubuntu`; on the two edition machines measured it says `ID=sparky`, and on the second the debconf answer is true, so who removed the files there is not known.
  **Fix (0.1.46 as rebuilt):** a gone file is counted in the summary and listed as `GONE` by `--deep`, never a problem ([why](#why-a-gone-file-is-no-fault)).
  **How found:** ucf's records read on two edition machines in daily use, each path tested for existence.
- **Symptom:** a test's `dpkg-stereo --verify --deep NAME` rows never appear, and a check that compares its exit status with a baseline passes; the log says `dpkg-stereo: error: unrecognized arguments: NAME`.
  **Cause:** `--verify` takes the package names after it, and `--deep` after it ends that list, so the names are left over and the run is refused with exit 2, the same as the baseline that was refused the same way.
  **Fix:** `dpkg-stereo --deep --verify NAME`, as the console's tests write it; a check on the exit status also requires the summary line (`^dpkg-stereo: `), so a refused run cannot pass. **How found:** the first run of ucf-test.sh's U4: the two `GONE` rows failed, and the FAIL lines showed the usage text.

An lc1 package's conffile that Lean Code does not project (it has no comments to remove: the console's `/etc/motd`, `/etc/skel/.selected_editor`) is named only by `--verify --deep` (`AFTERINST`), which needs that package's .deb (APT's cache first); with no network and no cached .deb the row is `NODEB`. A projected one (`/etc/skel/.bash_aliases`) is named by `--verify` itself (`LCCHANGED`).

## Diversions in the link and start gate

`lean/archive.py` reads the authenticated preinst. It authorizes a redirection only for the three exact forms below. Each uses `/bin/sh`, `set -e`, an install-or-upgrade guard and `exit 0`.

- A loop over literal absolute paths. Each path receives the same literal suffix.
- Consecutive commands with literal source and destination paths. A preceding `mkdir -p` may create the exact destination parent.
- A literal path assigned to one variable, a `dpkg-divert --listpackage` read into `before`, a diversion with a literal suffix and a guarded move of the pending `.dpkg-new` to that suffix's `.dpkg-new`. The guard tests for an empty `before`, an existing source and an absent destination.

The archive's package name must equal the package named by the diversion. The result binds that package, source, destination, archive hash and preinst hash.
The owning package's data goes to the diverted name. The declaring package's data can occupy the original name.
The gate assembles data from archives and has no pending dpkg conffile state, so the last form requires only the static mapping.
An unmodelled preinst grants no redirection and its reason appears in `diversions.json`. The usual path and collision checks apply to every package.

When another form is needed, retain the exact archived preinst in the tests. Compare the root assembled in both archive orders with a separate `dpkg-divert --root SCRATCH` oracle. Assert the link target and both payloads. Include near-miss scripts that vary the variable, moved path, suffix or owner, or insert a command. The parser must refuse them.

**Trap.** A valid pending-conffile script could make the data-only gate fail at the boot symlink while dpkg installed both copies. Reading `diversions.json` and the authenticated boot 0.1.16 preinst found the unsupported command sequence. A two-archive real dpkg unpack and the oracle fixed the expected file layout. Add the bounded form to the parser and run `PYTHONPATH=sparky-os python3 -m lean.release check-diversions POOL` before the long gate. A payload overlap or unresolved addition in an unmodelled script fails the pre-check. See the [small round check](../../edition-packaging/references/publication-round.md#prepare-both-link-gate-views-and-check-a-small-cohort).
