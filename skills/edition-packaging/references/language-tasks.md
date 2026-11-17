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

## Ordinary updates and the pending interval

A migration that needs a command from the person does not cover ordinary package updates.
Keep the aggregate's existing recommendation set stable so that upgrading a machine with removed languages does not add new task recommendations for those languages.
Make the language runtime a dependency and queue the work from its postinst, independently of the frontend.
Use the existing deferred-work pattern: a queue file, a path unit and a oneshot which waits for apt/dpkg locks before starting a new apt transaction.
Enable the units for the next boot even when building an image without a running systemd.

Before the original apt operation ends, capture installed language payload roots and their installed dependency closure and write temporary APT::NeverAutoRemove protection.
Changing apt marks inside a maintainer script is insufficient: the outer apt operation may rewrite its extended state when it ends.
After the locks are released, make the realized roots manual, install the retained language tasks and current tasksel/data, allow only the old wrappers in Remv, then check autoremove before removing the temporary protection.
Keep the queue and protection if the transaction fails, with a translated problems-engine notice.

Selection must honor the Locale tool's saved retained set.
For an older installation without that set, a shared regional package alone must not select a removed language: identify each language by its unique installed packs, plus the system language and English.
If the person adds or removes a language before the worker runs, update the queued selection too.
Resolve dictionary virtual names to installed providers when removing payload, rather than leaving the provider behind.

Prove old wrappers, a trimmed system and an all-language image against the actual signed edition, Debian and deb-multimedia indexes with the generated edition policy.
Retain Inst and Remv lines, the post-package/pre-worker autoremove plan, configured closure checks and the built catalogues in all ten languages.
A successful source build or a minimal resolver fixture is not that proof.

## Traps during implementation

- **Symptom:** a language-only meta build fails looking up an unrelated OS-developer package.
  **Cause:** the generator eagerly resolves every role's dependencies before honoring the selected output set.
  **Fix:** defer unrelated development-only resolution for an explicitly selected build.
  **Found by:** the missing plasma-wayland-protocols key while building only language tasks against the published index.
- **Symptom:** the meta generator rejects libreoffice-l10n-ar as a versioned library.
  **Cause:** its broad library-name expression matches the digits in l10n.
  **Fix:** distinguish LibreOffice data and named language plugins from ABI library packages.
  **Found by:** the language control generation error and the package's actual role.
- **Symptom:** a new container cannot reach the edition repository although its parent container could.
  **Cause:** Docker-managed hosts-file entries are not retained by docker commit.
  **Fix:** pass the required repository host mapping to each test/build container.
  **Found by:** failed edition downloads after successful Debian downloads and the new container's name resolution.
- **Symptom:** the installer package builds and the real archive link gate refuses it.
  **Cause:** the current recipe already requires package versions newer than the published universe, and another required package has no published candidate.
  **Fix:** retain the gate failure and required-versus-published versions and stop qualification until those dependencies are published or explicitly supplied as an authorized coherent cohort.
  Never weaken an unrelated designed dependency to turn the gate green.
  **Found by:** the gate's solver log, then apt-cache policy against the same signed sources and pins.

The deferred migration and task-aware Locale integration remain candidate implementation until their real installed-machine and complete package gates pass.
