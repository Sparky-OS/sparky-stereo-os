# Carried from Debian unstable

Use this when a base package has disappeared from testing.
Absence from testing does not by itself decide what the edition ships.

## Read the reason, then build

1. Resolve the binary to its source from the signed Packages/Sources indexes or `apt-cache showsrc` in a container with the edition's sources.
   Check `apt-cache policy` too: a version at priority -1 exists and may be blocked by our own policy.
2. Read Debian's [removal log](https://ftp-master.debian.org/removals.txt) and the previous years' `removals-YEAR.txt`.
   Preserve the source name, date, bug number and complete Reason field.
   The current year is in removals.txt; its separate year file may not exist yet.
   No entry in this log does not establish that a testing auto-removal had no cause.
   An older removal can also have been superseded: read the latest changelog and signed source index before carrying its old reason forward.
3. Read the source's [suite history](https://sources.debian.org/api/) and [britney's migration excuses](https://release.debian.org/britney/update_excuses.html).
   Britney names the bugs currently preventing migration.
   Debian's [Developer's Reference, release-critical bugs](https://www.debian.org/doc/manuals/developers-reference/developer-duties.html#manage-release-critical-bugs) explains why serious, grave and critical bugs can block a package.
4. Read each named bug's state and messages over the BTS SOAP interface as [contrib-debian](../../contrib-debian/SKILL.md) describes.
   `get_status` and `get_bug_log` can differ from an older web summary.
   Preserve severity, done, found_versions and fixed_versions, including empty fields.
   SOAP responses can contain maps with named children and base64Binary strings; decode according to the XML type, not the apparent text.
5. Search the newest Debian packaging and upstream default branch, merge requests and issues before writing a fix, as [search-upstream-first](../../search-upstream-first/SKILL.md) says.
   Keep a carried fix's author and origin.
   A vendor's fixed release may be newer than Debian unstable.
6. Classify the result:

| Evidence | Action |
| --- | --- |
| Renamed, superseded, or ended upstream with a living replacement | Keep the old name out, quote the reason and identify the replacement. |
| Living source, absent only from testing; SparkyLinux does not provide it | Carry a functioning fixed build through the edition pipeline. An unresolved security or runtime defect is work to fix before shipping. |
| Version exists but our pin prevents installation | Repair the relevant policy or task selection; do not rebuild a package merely to conceal our pin. |

7. Record the original `.dsc` hash and all files named by it from the signed source index.
   Use the source from unstable, its existing packaging and its existing fixes.
   Carry additional upstream fixes with DEP-3 headers.
   Obtain and verify a release signature when the vendor publishes one.
8. Apply [provenance](../SKILL.md#provenance-daniel-2026-10-02-always), then source preparation and Lean Code as [rebuilt packages](rebuilt-packages.md) describes.
   Pass the host's build facts with `build-provenance.sh`; preserve the source date.
   Build every architecture from the one prepared `.dsc`.
   `lean.release check-debs` must write a complete build record after `.buildinfo` and `.changes` exist.
   The archive-backed link/start gate and the installed proof below are separate requirements.
   If a metapackage depends on another carried source, supply its already qualified runtime archives through `SPARKY_LC_SIBLINGS_FILE`.
   Record the explicit sibling paths, copy without hard links, and let the gate hash/resolve that cohort against the published archive.
   Missing published dependencies do not justify dropping an enforcing metapackage or enabling sid binaries.
9. Stage the exact qualified binaries, source, HR companions and records with SHA256SUMS and a `.keep` explaining what awaits publication.
   A source input or a patch that applies is not a qualified package.
   Keep its base-gone row until publication; name the rows the publisher should then remove.
10. Compare every staged binary with the last published version, or Debian's matching original when the edition never shipped it.
    Save `dpkg-deb -c` of both and account for every removed entry, including directories, services, helpers, manuals and debug members.
    New HR companions have no Debian predecessor; keep their complete candidate lists and state that fact.
    A passing model-count check alone can conceal a missing helper or model family.
    For build-ID debug paths, map each removed ID to the original ELF and its replacement ID with `readelf -n`; do not call them harmless without checking the replacement exists.
    For generated CUPS driver archives, run both `list` outputs inside containers and compare complete archive identities, retaining their numeric member indices.
    A helper alias and reported driver-version text may change; record that normalization explicitly.

## Versions and retirement

For a backport on Debian revision `3.26.4+dfsg0-4`, use the established rebuild suffix, for example `3.26.4+dfsg0-4+stereo3d1+lc1`.
Check with `dpkg --compare-versions` in the build container that it is above the unchanged Debian revision and below `3.26.4+dfsg0-5`.
An upstream update packaged for the first time follows [Paweł's formula](sparky-formula.md); choose its revision below Debian's first packaging of that upstream version.
An invented higher epoch would prevent retirement and is not a solution.

Debian-native sources need a separate check: their next upload can be `BASE+nmu1`, not a hyphenated Debian revision.
The ordinary `BASE+stereo3d1+lc1` sorts above that native NMU.
For the checked native carries use `BASE+0stereo3d1+lc1`: it exceeds BASE while sorting below `BASE+nmu1` and the next maintainer version.
Measure both comparisons with dpkg; do not assume that passing the next-main-version comparison covers an NMU.
See Debian's [native NMU version rules](https://www.debian.org/doc/manuals/developers-reference/pkgs.html).

The version comparison alone does not retire ours.
The edition normally pins its origin at 1001 and blocks other builds at -1.
When testing has the fixed version at our version or newer, withdraw the carried build from the next repository snapshot, remove its names from the generated block list and publish the updated apt policy in that same round.
With the old version merely installed at priority 100 and Debian testing available at 500, apt upgrades to the newer Debian version.
Measure that transaction using the actual generated policy, including a machine on which the carried version is already installed.
Until that retirement, prove that the edition's build is the candidate.

## The installed proof

Use fresh testing containers with the edition's signed sources, published tree, current generated pins and a local candidate repository.
Keep sid's source indexes separate from binary sources; the proof must not satisfy missing runtime dependencies by silently enabling unstable binaries.
Read the `Inst` and `Remv` lines of `apt-get -s install`, then perform the installation.
Require the expected versions to appear in `Inst`, no removals, and a clean `dpkg --audit`.
A dry run with no removals can still have held every candidate back.

For HP printing, install the complete HPLIP binary family used by CUPS and the base set.
Start CUPS inside the isolated container, require `lpinfo -m` to enumerate HP models, and check the executable HP CUPS backend and filters.
This qualifies model discovery and loading, not a physical printer or scanner.
For Xorg drivers, load each installed module during a headless Xorg start with a dummy display and read its server log.
Do not claim a real VMware or QXL device from a dummy display.
A loader success also cannot establish that a build retained its KMS or rendering path: inspect configure's feature decisions and the linked dependencies.

## Cases checked on 17 November 2026

- HPLIP `3.26.4+dfsg0-4`: britney names open grave bugs [1148269](https://bugs.debian.org/1148269) and [1153419](https://bugs.debian.org/1153419).
  The first is the security report for CVE-2026-91097 through CVE-2026-91106; the second asks to restore current HP printer support to testing.
  [HP's bulletin](https://support.hp.com/us-en/document/ish_15646959-15646984-16) names 3.26.6 as the fixed release.
  Rebuilding sid unchanged would retain the known defects.
- QXL `0.1.6-1.1`: britney names open grave bug [1137518](https://bugs.debian.org/1137518), in the same source's xserver-xspice binary.
  Frank Heckenbach supplied a patch to initialize option defaults after `xf86ProcessOptions`; upstream [issue 16](https://gitlab.freedesktop.org/xorg/driver/xf86-video-qxl/-/issues/16) describes the zero SurfaceBufferSize and crash.
- VMware `1:13.4.0-2`: britney names open serious bug [1112670](https://bugs.debian.org/1112670).
  Debian dropped libxatracker-dev because Mesa removed XA; the driver's configure then disables its vmwgfx path without that dependency.
  Upstream [issue 12](https://gitlab.freedesktop.org/xorg/driver/xf86-video-vmware/-/issues/12) describes the resulting failure.
  Ian Forbes's [deprecation proposal 21](https://gitlab.freedesktop.org/xorg/driver/xf86-video-vmware/-/merge_requests/21) advises against shipping it with Mesa above 25.0.
  That merge request is open, not an accepted deprecation commit.
  Do not call a NULL-pointer guard a restoration of the missing driver path.

The QXL candidate was subsequently built through Lean Code and installed by apt in testing with the edition's pins; its module loaded in a headless Xorg dummy session.
For Xspice, the unchanged Debian source's module aborted with zero surface size, while the patched module reached a live display and stopped cleanly.
The red/green comparison used extracted module payloads, separately from the installed-package proof; it does not establish physical QXL-device behavior.
HPLIP was also built through Lean Code: 11 runtime packages passed the archive-backed link gate, and 22 archives passed check-debs with a complete build record.
A fresh testing container installed the complete 11-package family without removals; CUPS listed 5,732 HP models, backend discovery and hp-info help ran, and cupsext/hpmudext imported.
This does not establish physical printing, scanning, plugin installation, or GUI behavior.
The unchanged Debian source and candidate emitted the same 53 dat2drv diagnostics, so those diagnostics alone are not evidence of a newly introduced projection defect.
VMware stays excluded for that measured loss of its required component; no edition VMware package or retired XA stack is built.
Its kernel vmwgfx DRM/KMS driver can serve KWin directly on Wayland and Xorg's modesetting driver on X11.
That source-based path is distinct from a VMware guest/hardware test; issue 12 also reports autofit limitations, so no equivalence claim follows from choosing modesetting.

printing-metas `0.20210903` remains in sid and its migration is invalidated by HPLIP; its only open source bug, [1126396](https://bugs.debian.org/1126396), is normal.
Both native metapackages were carried with their unchanged dependency list; a fresh testing container installed all twenty recommended driver packages through the enforcing sibling, with no removals.
apt-xapian-index was reintroduced in 0.57, despite the older removal reason that called it obsolete.
Its 0.59 source is blocked by serious open [1145121](https://bugs.debian.org/1145121).
Santiago Vila's patch corrects test discovery; the complete checked fix also replaces removed unittest aliases and the removed libept-dev fixture with dpkg.
All four rebuild/incremental tests pass; the installed indexer builds an index and finds dpkg in a fresh testing container.
These are staged/installed proofs, not publication claims.

## Keep exclusions under observation

The ISO build's `iso-build/check-base-gone-sources.py` reports source presence for every excluded binary using an explicit historical binary/source registry and the Debian Sources API.
Run it before the base build and before a separately resumed package step, alongside the existing binary candidate gate.
It highlights sources alive only in sid; a source present in testing may instead have renamed binaries or retired transitions.
Network failures and unknown mappings fail, and are printed as unknown rather than absence.
Retain a dated response snapshot and test both a source returning to sid and lookup/coverage failures.
The first audit found the reintroduced apt-xapian-index, so its stale 2025 exclusion was corrected before hand-back.

## Traps

- **Symptom:** no removal-log entry, yet migration remains blocked.
  **Cause:** unstable removal logs and testing auto-removal/migration policy answer different questions.
  **Fix:** read britney and the source's RC bugs too.
  **Found by:** all three sources remained in sid while britney named their open bugs.
- **Symptom:** a SOAP decoder produces anonymous lists instead of severity and fixed_versions.
  **Cause:** it treats every non-leaf as an array; BTS maps also contain named children.
  **Fix:** distinguish item arrays, key/value maps and named structures, following href references and xsi:type encodings.
  **Found by:** comparing decoded output with get_status XML containing explicit field names.
- **Symptom:** a published-tree bind mount fails at a symlink with permission denied.
  **Cause:** that Docker mount could not resolve the alias, while the resolved repository directory was mountable.
  **Fix:** resolve the alias read-only, record the selected snapshot, and bind that actual directory read-only.
  **Found by:** the resolved-path mount probe succeeded; the alias mount failed.
- **Symptom:** apt rejects a signed archive because its named `.gpg` keyring does not exist.
  **Cause:** assumed key filenames differed from the packages' actual `.asc` and `.pgp` payloads.
  **Fix:** extract and inspect the public keyring packages, name their actual files, then retry signature verification.
  **Found by:** reading the extracted keyring payloads; no signature check was disabled.

- **Symptom:** the security backport fails to compile because `m_PrinterBufferSize` no longer exists.
  **Cause:** Debian's earlier buffer-growth patch left a cleanup assignment while HP's newer fix replaced the field with a size_t member.
  **Fix:** carry the corresponding upstream cleanup as well.
  **Found by:** compiling the merged source, then comparing the field declarations, constructor, cleanup and allocator with HP 3.26.6.
- **Symptom:** dh_install stops on an empty D-Bus or polkit installation glob.
  **Cause:** the security-fixed upstream removed the privileged plugin service, while the older Debian install manifest still required it.
  **Fix:** remove only the install entries and manual-page entry for the retired service and its now-empty directories.
  **Found by:** the binary build reaching dh_install after compilation, then checking the upstream removals against the manifest.

- **Symptom:** a native carry passes the next-maintainer-version check but exceeds Debian's next native NMU.
  **Cause:** +stereo3d sorts above +nmu; there is no Debian revision field in a native version.
  **Fix:** use the measured +0stereo3d carry suffix and test both +nmu1 and the next maintainer version.
  **Found by:** dpkg comparisons for printing-metas and apt-xapian-index.
- **Symptom:** an enforcing printer metapackage fails the archive gate although HPLIP was already qualified.
  **Cause:** the published snapshot does not yet contain the other staged source.
  **Fix:** pass the exact qualified HPLIP archives as explicit gate siblings, retaining the dependency set.
  **Found by:** reading the gate's apt solve, then rerunning with the existing sibling mechanism.
- **Symptom:** an exclusion still says orphaned/obsolete although unstable has a current source.
  **Cause:** a historical removal was kept after Debian reintroduced the package.
  **Fix:** read the new changelog and current migration blocker, carry the existing fix and qualify the revived source.
  **Found by:** the all-row source audit exposed apt-xapian-index 0.59 and its 0.57 reintroduction.
- **Symptom:** nose2 runs Python's own standard-library tests, then the corrected discovery exposes missing assert_ and libept-dev.
  **Cause:** ambiguous test-module discovery, removed unittest aliases and an obsolete package fixture.
  **Fix:** Santiago Vila's `-s test` discovery fix, current assertTrue calls, and dpkg as the replacement fixture; retain all four tests.
  **Found by:** unchanged source failed, the bug's partial patch exposed the remaining errors, and the complete patched suite passed in testing.
- **Symptom:** a CUPS catalog comparison reports too few unique entries.
  **Cause:** normalizing away the archive's numeric member index collapses different entries with the same PPD path.
  **Fix:** compare the full numbered URI and normalize only the known helper alias and driver-version text.
  **Found by:** 2,746 listed HPLIP archive entries collapsed to 892 paths; the corrected full catalog comparison retains all entries.
