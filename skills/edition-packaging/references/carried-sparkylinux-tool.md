# Carry a specifically authorized SparkyLinux tool version

A recorded edition decision may authorize a stereo version of an unchanged package name instead of changing SparkyLinux's release identifiers.
Keep the original published package and source pinned by version, revision, URL and SHA256; never rewrite the upstream archive.
For the display-name decision, sparky-about 0.1.49 and sparky-system 0.1.9 become +stereo3d1+lc1.
This permission covers one OSCODE assignment in each tool, not a general rewrite or an upstream submission.

## Recipe

1. Download the published binary and its exact Git source revision.
   Compare every payload file against the source, using explicit path mapping for bin, lang, share, icons and copyright.
   Fail on an unmatched or unequal file before applying the change.
2. Replace exactly the unique recorded line and retain every other payload byte.
   Preserve the upstream licence, author and package metadata through the normal provenance pipeline.
   Add names-only ATTRIBUTIONS, the stereo version, the edition provenance and Lean Code companions as usual.
3. Build the source package once, rebuild its binaries from that .dsc and compare payload and control trees.
   Run the normal Lean Code gate and retain the build record.
4. Put origin priority policy in its existing central owner, sparky-stereo-apt.
   SparkyLinux's sparky-apt has o=SparkyLinux at 1001.
   The two named tools use o=Sparky Stereo OS at 1002, without raising priority for other packages.
   Prove candidates with apt-cache policy using the real upstream archive and the staged local archive's proper Origin.
5. Install the actual archives through apt, check no removals and run both tools.
   Capture real UI text against edition and stock release files and compare the runtime scripts' authored HR forms with their originals.
   Distinguish the one functional source change from required provenance and Lean Code projection differences.

Retire the carry only after the base tool itself displays the correct name and the same edition/stock tests pass.
Nothing in this recipe authorizes sending patches or changing the base distribution's internals.

## Traps

- **Symptom:** an update takes the base distribution's version despite the stereo suffix.
  **Cause:** origin priorities are applied before version ordering.
  **Fix:** inspect all installed preference files and compare policy with both origins available.
  **Found by:** sparky-apt's priority-1001 preference, followed by the staged native policy check.
- **Symptom:** rebuilding a standalone recipe records a dirty source or an unrepeatable date.
  **Cause:** packaging before committing the working step or omitting build-provenance.sh initialization.
  **Fix:** commit first, initialize provenance from the recipe's commit and rebuild the .dsc, not a second independently assembled tree.
  **Found by:** reading the package's embedded sparky-build.json and checking source-rebuild equality.
