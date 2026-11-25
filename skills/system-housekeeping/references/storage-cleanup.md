# Preview and measure a storage cleanup

**For** contributors to Storage Cleanup in KDE, use the fixture to prove what can be selected, what space an item releases and what needs to stay.

**Check freshness first.** The edition's intended integration uses BleachBit as the engine. The independent `tools/storage-cleanup` program is a measuring fixture. It accepts only a marked isolated tmpfs in a container.

## BleachBit in System Settings

Look for the edition's BleachBit successor before using these switches. The Debian 6.0.6-1 control rejects `--json`. The edition patch lives in `sparky-os/packages/bleachbit/patches/structured-preview.patch`. The engine's installed entry point is `/usr/bin/bleachbit`. The page runs the same executable for the person and invokes it through the fixed polkit helper for administrator use.

```sh
bleachbit --json --list-cleaners
bleachbit --json --preview --volume / --preset
```

The first command returns BleachBit's cleaner names, their option descriptions and warnings, and flags from `[tree]` in the current account's `~/.config/bleachbit/bleachbit.ini`. The edition puts its initial user copy in `/etc/skel` and creates the administrator's file on the first housekeeping install when none exists. `--set-option cleaner.option true|false` edits this same tree through BleachBit's Options API. Reopen the catalogue to check a write. A running copy of the GTK window may still hold its prior in-memory selection.

The preview exposes the cleaner and option, the path, the action label, allocated bytes, the filesystem estimate flag and an item ID. Use Linux mount IDs from the opened path for scope. Checking only the pathname prefix would include files on a nested mount. Count `st_blocks × 512` for file allocation and distinguish it from logical length or space still referenced by snapshots. At confirmation, BleachBit regenerates the commands and matches the approved IDs to the mounted volume and file identities. Temporary files have a seven-day first age and are rechecked under a write lease. A lease refusal leaves the item in place. Scope-aware APT preview reads APT's configured directory and respects APT's POSIX lock. Detailed errors accompany the preview or confirmation result.

Journal vacuum can remove archived journals containing the current boot. Scoped cleanup refuses it and also refuses direct cleanup of persistent and volatile journal storage and core-dump directories. The checked journal preference remains visible in the catalogue. Browser bookmark backups and locally stored mail may be in the supplied preset. Show what each chosen entry removes before confirmation.

The edition's free-space notifier supplies the threshold and recovery observation. The Problems engine keeps the volume and an action to open its preview. Use a Problems action for that UI step, since a successful `repair` command normally deletes the record immediately. Clearing belongs to the existing notifier after the volume recovers. Weekly actions open a preview, and temporary files are never taken by an unattended run.

## Integration traps

| Symptom | Cause | Fix and how to find it |
|---|---|---|
| Stock BleachBit rejects the JSON command | The CLI renders human-readable summaries from the Worker | Run the new test on the extracted Debian control before applying the patch. Inspect Worker command dispatch for paths and operation IDs. |
| German or Portuguese KCM title with an English page | Setting only `LANGUAGE` left the C locale active | Generate and use the real session locale in `LANG`. Verify both the Qt page and BleachBit's catalogue. |
| File checkboxes appear without their labels | The Kirigami version in the rig exposes no `Format.formatByteSize` object there | Read the QML exception and use the linked KDE `KFormat` method to format each count. |
| A mounted location opens the cleanup page but the volume selector shows the system volume | `QStorageInfo(path)` accepted the mount but `mountedVolumes()` omitted it | Remember the validated activated mount in the selector's model. Compare the same direct launcher and mounted path before and after the change. |
| The package's main binary is removed by Lean Code | The archive link gate requires a working namespace runner. The default container disallowed user namespaces, and the explicit namespace probe could create one but could not mount `/proc` | Run the exact bubblewrap preflight and retain its exit before scheduling the package build. Use the edition's authorized namespace runner for qualification. |
| The low-space record disappears when its preview opens | The Problems `repair` verb considers a zero exit to be a successful repair | Give the record a named preview action. Feed the record's clear from the notifier's recovery branch. |

The scoped BleachBit feature and the page were exercised in a container. Drive paths in an installed edition Plasma session and package qualification need their own proof.

## Working recipe

1. Compare published package files and maintainer scripts with the build recipe.
   Find any maintenance timer, installed preset or policy that acts on the same files.
   Keep boot pruning, journal retention, crash retention and KIO wastebin settings with their owners.
2. Use the [build repository](https://github.com/Sparky-OS/sparky-stereo-os-build) checkout with the milestone's `tools/storage-cleanup` code.
   Point `DOCKER_HOST` at the authorized isolated Docker socket.
   Set `CLEANUP_FIXTURE_STAGE` to an existing writable directory and `CLEANUP_FIXTURE_CONTAINER_IDS` to a file for full container IDs.
   Use an allowed private mount and PID namespace.
3. Run the following from the build checkout.
   The default output is a new UTC-stamped child of the stage directory.
   A passing run writes 47 measured verdicts, one cross-mount verdict and one unmarked-root verdict, all `PASS`.
   It also writes both preview formats, a failure receipt, the protected-file inventory and start and end load averages.

   ```sh
   tools/storage-cleanup/rerun.sh
   ```

4. Check `measured.tsv` before describing a byte count.
   The fixture independently reads free blocks before and after applying each selected item.
   The sparse control has a logical size of 1 MiB and only 4,096 bytes allocated.
   An old open temporary file, a memory-mapped file, an ordinary personal temporary file, a matching name with no producer record and a document stay out of the preview.
   A valid item made unwritable after preview returns a reason and exit status 1.
5. Read `foreign.tsv` and `unmarked.tsv`.
   A nested tmpfs under a candidate-looking name generates a mount warning and keeps its planted file.
   An unmarked tmpfs refuses preview.

## Where to look and what removal costs

| Kind | Owner and usual location | Loss and scope |
|---|---|---|
| Completed package downloads | APT, normally root in `/var/cache/apt/archives` | Reinstallation may require another download. The fixture holds the APT-style POSIX lock and selects individual archives, leaving `partial`, startup policy, package lists and installed packages alone. A real helper must read APT's configured archive directory and use system authorization. |
| Thumbnails | The user's XDG thumbnail cache, usually `~/.cache/thumbnails/<size>` | Generated previews return as needed. The fixture uses the `normal` bucket. Source media and stereo choices stay. The [Thumbnail Managing Standard](https://specifications.freedesktop.org/thumbnail/latest/) defines other buckets. |
| Browser cache | The browser's own generated cache, with a fixture example of Firefox's `cache2/entries` under the user cache | The browser rebuilds it and may download data again. Profile settings, history, saved sessions, passwords, recovery files and reports stay. Discover an installed profile and test a closed and running browser before enabling an adapter for it. |
| Application cache | The app's own generated cache, with a Mesa shader cache example under the user's XDG cache | The application will rebuild it. The fixture checks one cache bucket. App settings, games and user state stay. |
| Application temporary files | A known producer's own directory under `/tmp`, with the same user rights in the fixture | The temporary data is gone. Require a producer record for the exact file, elapsed age and a closed, unmapped file. There is no blanket scan, no automatic temporary cleanup and no change to the `/var/tmp` rule. |
| Trash | The user's `$XDG_DATA_HOME/Trash` and per-volume Trash under KIO | Restore is lost for the selected item. The fixture measures one regular item and its paired `.trashinfo`. The desktop should use KIO for operations, restore consistency and the existing age and size settings. See the [Trash Specification](https://specifications.freedesktop.org/trash/latest/). |
| Rotated logs and previous journals | The service or the root-owned rotation and journal stores in `/var/log`, with volatile journals under `/run/log/journal` | Logs are diagnostic evidence. Measure representative allocated bytes without offering removal. An archived journal may still contain current-boot messages. Preserve the current start and report evidence before evaluating any owner-managed action. |
| Crash dumps | systemd-coredump's journal and usually `/var/lib/systemd/coredump` | Removing a dump can make diagnosis impossible. The fixture plants crash evidence to prove exclusion. The retention policy stays with the crash handler. |
| Unused Flatpak runtimes | Flatpak or OSTree in `/var/lib/flatpak` or the user installation under `$XDG_DATA_HOME/flatpak` | Runtimes may need to be downloaded again. A runtime's displayed size does not represent its unique objects. Measure an explicit per-installation Flatpak or libflatpak operation on a repository with both shared and unique objects before labeling bytes reclaimable. |

## Engine rules

- Walk from a directory descriptor and keep it open through the operation.
  Open each component with `O_NOFOLLOW` and require the root mount ID and device.
  Consider regular single-link files of the expected owner.
  The prototype pins candidate descriptors and checks that the pathname still names the previewed inode.
- Report `st_blocks × 512` allocated bytes and keep logical size separate.
  On the idle fixture, compare with the independent `statvfs` free-block delta times fragment size.
  Shared blocks, filesystem snapshots, compression and concurrent filesystem activity need filesystem-specific evidence before claiming a real reclaimed size.
- JSON preview returns stable kind and item IDs, mount-scoped paths, allocated and logical bytes, a localized loss sentence and warnings.
  For `clean ID … < preview.json`, recheck the rule, path, inode metadata and current open-file status, and return a result for each ID.
  A nonzero exit signals a failure even when another selected item succeeded.
- Check descriptors and memory maps by device and inode in the fixture's PID namespace.
  If observation fails, refuse the operation.
  Rechecking immediately before unlink reduces the race.
  A real implementation also needs a producer lifetime protocol or equivalent writer exclusion before enabling temporary-file deletion.
- The application's normal user can select its own cache and Trash data.
  A privileged action should accept only a fixed scoped operation via the system's polkit agent.
  Keep one engine for every KDE entry point.
  Keep broad preset options, recoverable personal data and background promises out of the fixture and the first release.

## Traps

| Symptom | Cause | Fix | How found |
|---|---|---|---|
| The edition's `/tmp` no-age rule looks incompatible with an enabled BleachBit temporary checkbox. | The tmpfiles rule governs automatic aging and the preset governs a manually invoked tool. The preset also selects operations beyond storage cleanup. | Keep the policy and preset separate from the scoped preview. Require a producer record before offering a temporary file. | The numbered r1123a conffile and both INIs show the two triggers. |
| A 1 MiB file is expected to return 1 MiB. | Sparse logical length includes unallocated holes. | Count allocated blocks and check an independent free-block delta. | The planted 1 MiB sparse object frees 4,096 bytes. |
| A descriptor scan would classify a mapped file as closed. | A mapping can survive closing its original descriptor. | Search the fixture process maps by device and inode as well. | The fixture drops the descriptor, keeps the mapping, and verifies that the path stays out. |
| An old temporary filename matches but does not belong to the producer. | A naming convention says nothing about who created the file. | Require a producer record matching the file identity and revalidate it at apply time. | The second old file has the same name shape, matches the age rule and is absent from the preview. |
| A candidate-looking name hides a mounted filesystem. | A path string can name an entry on a different mount. | Compare mount ID as well as device after opening, and keep the traversal descriptor-relative. | The nested tmpfs case gives an explicit mount warning and the foreign file remains. |
| `tar (child): xz: Cannot exec` in the archive audit. | The minimal image's dpkg-deb could extract packages without the separate command that tar requires. | Supply a pinned decompressor in the audit environment and record its digest. | Package extraction succeeded before the source extraction failed at tar. |
| Checksum preparation reports `Read-only file system`. | Scratch output inherited the working directory of the read-only recipe mount. | Write intermediates inside the audit container's scratch directory and keep the recipes read-only. | The audit log named the first checksum scratch file that could not be written. |
