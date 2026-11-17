# Per-language tasks

## Reconcile before building

1. Read the supported-language map in the distribution's list generator, its generated package list, the installed metapackage's control fields and the edition's language design.
   Language coverage and the languages of the edition's own strings are different sets.
2. Obtain the exact Debian tasksel source version used as reference.
   Check its archive hash against its `.dsc` and read both `debian/control` and `tasks/`.
   For every supported language, tabulate the base, desktop and KDE tasks' Depends and Recommends, the edition's existing packages, and the difference.
   Keep absent tasks explicit: Malay is not Malayalam; Latin American Spanish shares generic Spanish application data and Debian's Spanish tasks; English includes regional desktop variants.
3. Resolve `${misc:Depends}` from the corresponding binary control or the debhelper integration, rather than omitting it.
   The tasksel 3.92 language binaries depend on `tasksel (= 3.92)`.
   Preserve alternatives and virtual providers when comparing names; a missing candidate for a virtual name does not establish an unavailable feature.
4. Propose one `task-sparky-language-<code>` task per language, using lowercase package-safe locale codes, and a shared dependency task.
   Put the chosen language's promised payload in Depends, including data that Debian only Recommends.
   Depend on tasksel without copying Debian's exact-version lock.
   Keep the comparison literal, then name each deliberate substitution against the edition's design: its Fcitx 5 engines replace Debian desktop tasks' IBus engines.
5. Prove the proposal with apt before building packages.
   A temporary file repository containing only proposed Packages records allows `apt-get -s` to test dependency resolution without building a binary.
   Distinguish that evidence from installation or maintainer-script proof.
   Simulate each language with `--no-install-recommends`, the complete image selection, a missing required package, and an old-task upgrade.
   Read every `Inst` and `Remv` line and keep exit codes.

## The Debian task pin and upgrades

The edition blocks Debian's `task-*` at negative priority and presents its own tasks.
Do not lift that pin to fix tasksel.
An installed Debian language task can require `tasksel (= OLD)` while its newer wrapper is blocked, holding tasksel back.
An explicit tasksel upgrade can remove the old language wrappers; without replacement dependency roots their automatically installed payload can become eligible for autoremove.

Before retiring a wrapper, record its installed Depends and Recommends providers and manual/automatic marks.
Protect the realized payload roots, including an installed alternative that the new design no longer needs, and install the replacement language task in the same apt transaction that retires the wrappers and upgrades tasksel and tasksel-data.
Conflicts on replacement tasks may identify the corresponding Debian wrappers, never their dictionaries or other payload.
Do not add Replaces unless files actually overlap.
Do not run apt recursively from a maintainer script.
The migration belongs in an explicit upgrade operation, with a saved plan, a removal allowlist limited to the old wrappers, and failure before mutation if anything else would leave.
A surviving unsupported Debian language task must be reported as a remaining lock, not ignored.
After the transaction, simulate autoremove with the old payload marked automatic except the protected roots and verify that none of the payload appears in `Remv`.

## Image, installer and the Locale tool

The image must continue shipping every language it already promises.
Install every language task explicitly from a checked manifest in the image builder, even if Recommends are disabled, and verify that each task and every required payload dependency is configured.
An aggregate metapackage that Depends on all languages would prevent the person's existing Locale tool from removing unused languages while keeping the edition's top metapackage.
Keep that removal path usable: the language tasks own the hard dependency promises, the image explicitly installs them, and the aggregate can retain recommendations.

After Calamares unpacks the image and writes the target locale, its language step must select and install the matching task in the target, mark it manual, and verify its dependency closure.
Do this for English too and verify an already partially translated language instead of using an "any pack exists" test.
Verify the copied task before refreshing remote indexes, so a complete offline image can finish without a network.
A missing required payload is an installation error naming the language, task and package; repair notifications alone do not prove that installation fulfilled the language promise.
The Locale tool's add and remove paths must understand the same manifest, task names and new dictionary families.
A deliberate removal retires the corresponding unused task before purging its payload, keeps the system language and English, and removes no shared dependency still required by a retained task.

## Traps

- **Symptom:** tasksel remains at the old version or upgrading it removes three language packages.
  **Cause:** old Debian task wrappers depend on its exact old version and the edition blocks their updates.
  **Fix:** replace the wrappers with the edition's language task, protect payload roots, and upgrade tasksel and tasksel-data together.
  **Found by:** installed control fields, apt policy and the simulation's `Inst` and `Remv` lines.
- **Symptom:** a language task installs without input methods or dictionaries when recommendations are disabled.
  **Cause:** the payload is only Recommends.
  **Fix:** put each task's promised payload in Depends and explicitly install image tasks.
  **Found by:** compare the generated control fields and run with `--no-install-recommends`.
- **Symptom:** a partial language installation is treated as complete.
  **Cause:** the old Locale tool stops planning additions as soon as any package of that language exists.
  **Fix:** install and verify the language task's complete dependency closure.
  **Found by:** reading `plan_install` and its `have` test.
- **Symptom:** a Czech dependency has no candidate although the task resolves.
  **Cause:** `myspell-cs-cz` is provided by `myspell-cs`.
  **Fix:** inspect `apt-cache showpkg` and the provider's Conflicts, then prove the full dependency with apt instead of dropping the feature.
  **Found by:** the candidate report, its Reverse Provides section and the failing resolver plan.
- **Symptom:** making every reference dictionary mandatory makes Czech, Spanish, Norwegian or Ukrainian uninstallable.
  **Cause:** the MySpell dictionary in Debian's recommendation conflicts with the Hunspell dictionary the edition already ships.
  **Fix:** prefer Hunspell on a new image and allow the reference MySpell dictionary as an alternative on an existing machine; for Norwegian preserve both Bokmål and Nynorsk when using MySpell, including their hyphenation files.
  Protect installed roots explicitly during migration and refuse a plan that removes any payload.
  **Found by:** a literal-union Czech simulation, then both dictionaries' Conflicts and Provides fields; a Norwegian retention probe also found hyphen-no conflicts with both MySpell packages, whose archives carry the hyph_nb_NO and hyph_nn_NO files.
- **Symptom:** preserving every Debian desktop recommendation brings IBus back beside Fcitx 5.
  **Cause:** the reference package set was copied without the edition's input-method design.
  **Fix:** keep Debian's recommendations in the evidence table and map the four IBus language-engine entries to the edition's corresponding Fcitx 5 engines in the proposal.
  **Found by:** the edition's deduplication record and desktop task controls.
- **Symptom:** removing unused languages removes the top edition metapackage.
  **Cause:** an aggregate hard-depends on all language tasks.
  **Fix:** explicitly install image tasks and let the Locale tool retire unused task roots; keep hard dependencies inside each language task.
  **Found by:** following the top metapackage's dependency graph against the existing language-removal design.

- **Symptom:** a simulated install of an archived wrapper says "Can't find a source to download version".
  **Cause:** its copied binary control lacks the repository Filename and Size fields.
  **Fix:** retain the archive's real Filename and measured Size in the temporary Packages record, then refresh apt indexes.
  **Found by:** the old-task seed simulation; binary control fields alone are not a complete apt index.
- **Symptom:** Python HTTPS downloads fail after apt HTTPS setup succeeds.
  **Cause:** the apt helper configures apt's CA path; Python does not inherit that setting.
  **Fix:** point Python's SSL_CERT_FILE at the same mounted CA bundle; keep certificate verification enabled.
  **Found by:** the certificate-verification exception and the helper's apt-specific configuration.

- **Symptom:** applying an old-version solver plan to a status fixture fails with a missing `name=version` record.
  **Cause:** `apt-cache dumpavail` did not retain the explicitly selected archived version.
  **Fix:** merge the exact archived binary controls and proposal records into the metadata map before applying `Inst` lines.
  **Found by:** the seed selected tasksel-data 3.91 while the dump held its current version.

This reference describes the reconciliation method and proposal requirements.
Resolver simulations do not establish that new packages, the installer integration or the migration helper have been built or shipped.
