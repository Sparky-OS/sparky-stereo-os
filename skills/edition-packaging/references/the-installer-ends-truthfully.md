# The installer ends truthfully

An optional download has its own result.
A completed operating-system installation keeps its completion verdict, and the optional step says what was skipped, why and how to do it later.
An essential failure still stops the installer with its own error.

## Reconcile the published installer

1. Verify the published `InRelease` against the edition signing key.
   Use the authenticated Release hashes to verify the architecture's and `all` package indexes and the Sources index.
   Check the selected binaries and source closure hashes against those indexes.
   Compare each consumer's installed module and the provider's binary control with `dpkg-deb -x PACKAGE.deb DIR` and `dpkg-deb -f PACKAGE.deb`.
2. Follow the actual execution sequence in `/etc/calamares/settings.conf` and the matching module config.
   In r1123a, `shellprocess@corefonts` invokes the live `core-fonts --window` helper near the end.
   The round has the provider `ttf-mscorefonts-installer` from `msttcorefonts` 3.8.1+stereo3d2+lc1, with a declared download of 3,934,864 bytes.
   Compare the helper with the next staged settings package as well.
   The installed helper in 20261117.3+lc1 and staged 20261125.1+lc1 is byte-identical and returns an error to Calamares when its optional transaction fails.
3. Check `partition.conf` in the Calamares binary package and look for an override from the settings package.
   The r1123a partition module offers `none`, `small`, `suspend` and `file`, with `initialSwapChoice: none`.
   The fstab job writes a 512 MiB swap file for the explicit file choice.
   Read the fstab, initramfscfg and grubcfg jobs together.
   In this release grubcfg writes a GRUB `resume=` argument for a claimed swap partition.
   Those jobs write no explicit initramfs resume configuration for the file.
   The settings package calls `cushion-swap --adopt installer` after fstab, and Cushion Swap 0.3.5 reads the installer-provided `RESUME` and `RESUME_OFFSET`.
4. Read the live tool, its autostart entry and the generated systemd user unit's drop-in together.
   The keyboard package in r1123a already carries the live-only condition, as described in [a live-only autostart entry on an installed system](live-only-autostart.md).
   Read the package source descriptor and the recipe's source commit and tree fingerprint to identify where the guard entered.
5. Keep a control for the claim being checked.
   Remove the font provider's entry from a copy of the in-memory package list, remove one swap choice from a copy of the configuration and omit the live-only drop-in in a copy of the unit-input check.
   Each check must detect its missing input.
   These controls cover archive inspection.
   A production publication gate and a complete guest installer run require their own tests.

## Optional download and publication

Use the selected provider's `Sparky-Install-Download-Size` and `Sparky-Install-Download-Source` fields in the graphical notice.
Read NetworkManager before contacting the archive on the optional step's behalf.
A metered link holds the download and gives the later install command.
The connected case shows the size and source before consent, then runs the provider's own licence and download flow in the new root.

After a failed transfer, check whether this step introduced an unconfigured package.
Remove the package it introduced and report the optional loss.
Preserve a package already present and show how to finish its configuration.
Check dpkg's audit, the actual installed data and the next Calamares job in the test.
Report a failed cleanup with its own cause.

Use `Sparky-Install-Download-Requires` in the consumer's binary control.
Check selected binaries of the matching architecture before copying pool files or signing metadata.
A replacement provider must carry valid size and source fields.
The historical settings fixture also exercises a consumer which had the font module before the explicit field was introduced.

## Choose swap in the partition module

For a fresh automatic install, calculate the plan from the system disk selected on Calamares's partition page.
Show the file or partition sizes there and again on the summary page.
Keep the person's other choices available.
For drives above 256 GB the normal plan reserves a hibernation partition and a separate Cushion Swap file.
At 256 GB or less a single RAM-sized file serves both jobs.
Leave 20 GiB after the installation and its swap allocations.
If the selected disk lacks room, show the smaller swap area and say hibernation needs more space.

Write the Debian initramfs resume setting during the fstab job.
A partition has its swap UUID, and a file has its backing filesystem UUID and physical offset in kernel pages.
Reuse Cushion Swap's initramfs offset hook.
Keep the dedicated partition out of normal swap use.
The adopted file's `noauto` fstab line also stops the GPT auto-generator from claiming the partition.
Inspect `/run/systemd/generator.late` as well as the normal generator directory when tracing an unexpected swap unit.

For a machine that is already installed, expose the repair through the Problems page or the no-area notification.
Authenticate the action through the engine's polkit entry point.
The repair checks free space and the existing area's provenance before preparing a file, writes the resume settings and regenerates the initramfs when needed.
The availability item is a single root-kept record on the Problems page.

## What the installer run must establish

- Boot the published set and the successor in separate disposable guests, complete Calamares and keep the final page and the optional step's log.
  Use the same install-time size declaration as apt and keep the licence interaction described in [licensed data at install time](licensed-data-at-install.md).
  Cover installed fonts, no connection, a metered connection and a transfer that fails after it starts.
  Verify the target's package state as well as the wording the installer shows.
- Exercise the [publication-round](publication-round.md) gate with a consumer whose declared provider is absent, then with the provider present.
- Record the swap selected on the partition page, the resulting fstab and the initramfs resume configuration.
  For a swap file, verify the filesystem UUID and first-page offset.
  Follow the [hibernate guest proof](../../power-idle/references/hibernate-in-a-vm.md) to check that the image is written, the memory witness survives a new VM start, and swap stays off at boot.
  Compare `/proc/swaps` and both logind capability replies after boot, after resume and under memory pressure.
  Confirm which area each operation used.
- Read `systemctl --user --failed` after each of three installed logins and verify the keyboard setter still runs in the live session.
  Read target package ownership too, so a removed live package and a retained package with a working condition are distinguishable.

## Traps found in the archive audit

- **The package is in the archive and the old error can still occur.**
  The declaration repairs the missing-provider case, but the graphical helper still turns discovery, update or download errors into a failed Calamares job.
  Verify the archive separately, then drive the four connection cases in the installer.
  The evidence came from the signed Packages stanza and the two package payloads' identical exception and exit paths.
- **A 512 MiB file can be mistaken for the default.**
  The file is made only when the configured choice is `file`.
  Read the installed `initialSwapChoice` and check the selection in the running installer.
  The difference came from tracing the published partition configuration into fstab's `partitionChoices` handling.
- **A documented resume setting can be mistaken for an installer-written setting.**
  Cushion Swap documents and reads the setting and has a hook for the offset.
  Check who actually creates the configuration before initramfs generation and verify the result on the installed guest.
  The difference came from comparing Calamares's active job sequence with Cushion Swap's README and hook.
- **The keyboard command's exit 1 can be mistaken for a current login failure.**
  The installed command still rejects direct invocation outside live mode.
  Read the autostart-generated unit and its condition before proposing a change.
  The published bundle included the drop-in even though the command still had its original exit.
- **The signed Release comparison can fail even though the OpenPGP signature verified.**
  Sequoia's `sqv` can print the signer's fingerprint to standard output and write cleartext without its final line break.
  Send the verified text to a separate file, keep the signer fingerprint separately and account for the missing delimiter when comparing to the detached Release.
  The first comparison differed from the first byte, and the second differed only at the end of the last line.
- **A slim Debian inspection container may have `tar` but omit the `xz` program.**
  Use Python's `tarfile` with LZMA support to read source members directly and keep the source archive mounted read-only.
  The first source extraction reported `xz: Cannot exec: No such file or directory`.

## Traps found by running the installer and the guest

| Symptom | Cause and how it was found | Fix |
| --- | --- | --- |
| An archive solve omitted libdav1d and the live guest later lacked a formatter. | The resolver used Debian and SparkyLinux alone. The first Calamares job log also named an absent `mkfs.ext4`. | Include the signed deb-multimedia companion of the tested round and explicitly install `e2fsprogs` in a minimal live root. |
| GRUB's EFI helper could not download packages. | A build-only CA path survived in the guest's apt config. The HTTPS error and the missing mounted CA file identified it. | Point the installed root at its own CA bundle and include the EFI tools in the live root. |
| A full published run reached the language job and stopped. | Apt history showed the language task was installed as an automatic live-settings dependency and removed by the installer. | Select the actual language task, edition keyring and language tools explicitly when assembling the rig. |
| A finished ISO and its manifest were present after the packer returned an error. | The host script was edited while the interpreter was still reading it. The listed outputs passed their checksums and the guest booted from them. | Copy the driver and any mounted pack script before starting a long build. |
| KVM probed successfully as root and failed for the normal runner. | The KVM device's access was restricted to its group. Testing the numeric UID separately found it. | Pass only the KVM device and its group to the disposable runner. |
| Serial commands and evidence lost characters on the accelerated guest. | The emulated UART dropped parts of a burst. Whole-file checksums and a broken base64 frame exposed it. | Pace console commands and transfer logs through the private guest fixture channel with verified hashes. |
| The next connection case failed writing apt's cache. | Completed writable overlays accumulated in the live fixture's `/run` tmpfs. Apt reported ENOSPC and `df` traced it to that mount. | Read back the result, then unmount and clear each overlay before starting another. Size the fixture's tmpfs for a single complete target. |
| The optional outcome was unreadable behind a progress dialog. | An image of the metered case showed Qt showing the progress dialog again after the outcome opened. | Reset the progress dialog before opening the next message. |
| A guest with no fstab swap line booted with its hibernation partition active and Cushion Swap had no area. | The GPT generator's output contained a late `swap.target.wants` entry. Cushion Swap's status and fstab inspection identified the missing file. | Give Cushion Swap its own adopted `noauto` file. Re-run the generator to show that it stands down. |
| A complete hibernation left the dedicated partition active. | The marker and kernel log proved resume. The pageout control left ordinary swap pages in the partition, while the daemon's area was the separate file. | Switch off the area that hibernation activated once its pages fit back in memory. Keep an explicit problem when a dedicated area cannot be released safely. |
| The first pageout control stopped before writing a hibernation image. | The sleep unit journal showed that Python omitted the `mmap.MADV_PAGEOUT` constant. | In a Linux fixture use the documented ABI value, then require a minimum of resident swap data before proceeding. |
| The repaired swap file resumed correctly and remained active with 32 KiB in use. | QEMU recorded a shutdown and the witness survived. The old resume hook delayed release of its own occupied file. | Apply the same safe release to a shared file activated for hibernation. Keep the daemon's normal retraction when the system still needs that area. |
| The repair authenticated and then returned status 1 without creating a file. | The Problems record retained the exception from `Path.open()`, which does not take an `opener` argument. | Use the builtin `open()` with an owner-only file mode, then exercise the actual Repair button again. |
| A missing area still took processor time. | The service sampled PSI and ran calibration with no area. Compare `CPUUsageNSec` for the same PID over a fixed observation window. | Write the one outcome and wait for a real settings event. Verify that an fstab edit wakes the service. |
| A second guest could boot but the console controller could not connect. | Its nested host evidence path exceeded the Linux Unix-socket address limit. The short `/proof` path in the runner worked and the long host path failed before the first console command. | Open the socket with a relative name from the evidence directory, and keep the long path for ordinary saved files. |
| A successor installer summary continued below the screen. | The unmanaged X display used by the fixture was 1280 × 800. The actual summary image showed Storage Cleanup content below the fold and no navigation strip. | In that fixture, move the window until its navigation is visible before clicking Install. Drive the normal summary and preserve the recorded choice. |
| The first successor root solve failed with conflicting signing-key options. | Inspecting the target's source stanzas showed two entries for the same archive with different `Signed-By` values. Another solve was interrupted by a Debian CDN connection reset. | Start the comparison from the verified published SquashFS, keep its signed sources, and explicitly apply the candidate transaction using the same archive set. |
| A live-only helper appeared missing after installing the packer into a running session. | Plasma's existing systemd user manager had generated its units before the package was added. `systemctl --user cat` failed while the package already owned its desktop entry. | Reload the user manager or start a fresh seat session before inspecting generated units. |
| Starting the user unit returned before either the expected error or keyboard change. | The generated service uses `Type=exec`, so systemd acknowledged execution while the command was still making its checks. | Wait for the measured failure or read the actual keymap from an X server until it changes. For an independent Xvfb check, retain the keymap after the last client disconnects with `-noreset`. |
| Apt could resolve the packer with the retained index but failed to fetch edition binaries. | The minimal copied archive held the signed index and only the font binary. Apt also reported permission denied on a fixture download in a 0700 directory. | Transfer the listed edition files from the read-only signed cohort with SHA-256, and make the temporary parent directory traversable for apt's download account. |
| A light build image could read a source descriptor but could not rebuild it. | The first extraction had placed the upstream tarball inside the new extraction destination. The build then separately reported a git ownership check and missing `dch`. | Supply the tarball beside the descriptor, keep the extraction target new, and use a disposable builder with the checkout's ownership accounted for and `devscripts` installed. |
| One successful installed Plasma login was followed by sddm refusing another start. | The fixture deliberately restarted SDDM while the previous seat was closing. Once the old user manager was gone, the next clean start hit the system unit's start-rate limit. | End the old guest user manager, clear only SDDM's system-unit start budget, then measure the new session and the new user manager's failed units. |
| A resumed guest passed the pressure test and refused ordinary console poweroff. | The serial output named the still logged-in Plasma session as an inhibitor. The hibernation evidence preceded the shutdown request. | Use `systemctl poweroff -i` for cleanup inside the disposable guest after evidence has been read. |
| The attached Calamares build log ended during compilation. | The attachment exited 143. The source and binary outputs, complete build record and payload verification were independently present in the output directory. | Validate the source closure and staged binaries before treating an attach error as a build error. Retain the incomplete attachment log and the successful qualification evidence. |

## Boot checks, translated repair outcomes and Btrfs

A package that enables a boot check needs the usual debhelper maintainer-script lifecycle.
Use `deb-systemd-helper unmask`, `was-enabled` and `enable` or `update-state` on configure, then the matching stop, mask, purge and unmask paths.
A preset describes a policy. The package lifecycle creates the effective enablement link and respects recorded administrator choices.
Check a fresh install and the real upgrade. Reboot both and read the unit journal for the new boot.
Check dependencies and triggers separately. A static path can be active because a daemon wants it, and the service it triggers is normally inactive while idle.

The Problems page already knows its language and the repair command's exit status.
For a repair with specific outcomes, put a package-and-key mapping in the existing problem record's `repair_feedback` data.
Render the catalogue from that mapping as soon as the action finishes and when the page reloads a retained refusal. Keep the technical diagnostic in the journal.
Use real locales and exercise both a refusal and a successful authorized click. Close and reopen the page to verify that the instruction remains visible. An ordinary repair continues using the Problems page's generic text.
The engine and authorization path can stay the same.

On single-device Btrfs, use a root-owned separate subvolume for the swap file, outside the root's snapshot contents.
Prepare the file with `btrfs filesystem mkswapfile`. Its no-CoW file has compression off.
Run `btrfs inspect-internal map-swapfile -r` to validate the allocation and get the device page offset. Write the filesystem UUID and that offset to the initramfs resume file.
Use a fresh install and an installed-system repair as separate paths. Keep the file off in fstab and require an actual resume from it.
[Upstream Btrfs swapfile documentation](https://btrfs.readthedocs.io/en/latest/Swapfile.html)

For the occupied shared area, add test-only preparation after Cushion Swap's sleep preparation hook. Have a real process page its anonymous memory out after the hook enabled the file.
Keep the memory process and the witness alive across S4. Record used KiB before sleep and classify the release after the resume hook has finished.
An empty file can switch off with the empty-file message. A positive read-back must report a number greater than zero. A deferral keeps the file active and reports the headroom reason once.

| Symptom | Cause and how it was found | Fix |
| --- | --- | --- |
| The capability service was preset enabled after an upgrade, but its installed enablement state was disabled. | The maintainer script restarted the service without registering enablement through Debian's service lifecycle. The A10 showed the inactive enablement state. | Use the debhelper helper pattern and prove the new boot in both package-install paths. |
| A refusal showed a generic command error and a successful repair showed only the title. | The engine keeps the failed command output as evidence and discards successful stdout. The privileged process cannot determine the page's language from its own sanitized environment. | Carry the result mapping on the existing Problems record. Render by the page's language and retain the technical cause in the journal. |
| The kernel completed resume while the proof still found active swap. | The first serial sample preceded completion of the service's ExecStopPost. The journal had thawed the user slice and had no release line yet. | Wait for the resume hook's result, then read the swap table and the journal. |
| A good resume failed the older rerun when the shared file was empty. | The judge recognized only the occupied release wording. A replay compared the actual release line with the predicate. | Accept both successful release lines, and require a positive amount in the separate occupied test. |
| The serial console could start the hibernation witness but hibernate was refused. | Logind named the guest's other graphical login in the inhibitor diagnostic. | Request hibernate with `-i` only from the disposable serial-controlled guest proof. |
| The GUI authorized a repair, but the new Btrfs subvolume then failed the writable-mode check. | Starting the first build with umask 000 reproduced the interactive refusal on a missing /swap. The direct console test with the ordinary umask had passed. | Set a private umask in the repair and mode 0700 on the subvolume it creates. Validate existing subvolumes without changing their ownership or permissions. |
| The Problems page showed exit 127 before a repair could start. | The test had launched the GUI through a transient system service with the desktop UID. It had no graphical polkit agent in that authorization context. | Launch the test page through the existing desktop user's systemd manager, then authorize the actual action in the guest. |
| OCR could see the Hibernation title but missed the clicked Repair button on the next launch. | The guest screenshot showed the mouse pointer across the button text. | Park the pointer away from the window before reading OCR and select the button anchored to the actual hibernation item. |
| Reopening Problems replaced the translated repair instructions with a generic exit number. | The screenshot of the reopened German page showed status 40. The reload code read the retained status but did not use the record's catalogue mapping. | Resolve the retained status through the same catalogue helper as the immediate result. Show the guidance once while the banner is visible, then on the card when the page is reopened. |
| The offline Btrfs guest showed a language package download error above the hibernation problem. | An installed-seed screenshot showed the deferred apt job using the disconnected live proxy. | In the GUI fixture, record the unrelated language task's failures before clearing them and stopping its triggers. Keep the hibernation and repair paths active. |
| The old hibernation policy remained available immediately after the fixture removed its swap file. | The running logind still had its earlier generator environment. Restarting it by itself returned the guest to the greeter. | In a disposable test guest, tear down the old session before refreshing logind and start a fresh session for the page. Test the repaired setting on the subsequent ordinary boot. |
| The initramfs builder warned that the configured UUID did not match an active swap device. | The new Btrfs area was a noauto file. The on-disk config, physical offset and final package output supplied better evidence than the generic builder warning. | Read the same UUID and physical page offset from the installed file and require a real S4 cycle with a preserved witness. |
