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

## What the installer run must establish

- Boot the published set and the successor in separate disposable guests, complete Calamares and keep the final page and the optional step's log.
  Use the same install-time size declaration as apt and keep the licence interaction described in [licensed data at install time](licensed-data-at-install.md).
  Cover installed fonts, no connection, a metered connection and a transfer that fails after it starts.
  Verify the target's package state as well as the wording the installer shows.
- Exercise the [publication-round](publication-round.md) gate with a consumer whose declared provider is absent, then with the provider present.
- Record the swap selected on the partition page, the resulting fstab and the initramfs resume configuration.
  For a swap file, verify the filesystem UUID and first-page offset.
  Follow the [hibernate guest proof](../../power-idle/references/hibernate-in-a-vm.md) to check that the image is written, the memory witness survives a new VM start, and swap stays off at boot.
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
