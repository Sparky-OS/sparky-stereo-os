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
The queued worker performs the migration after an ordinary update, with a saved plan, a removal allowlist limited to the old wrappers, and failure before mutation if anything else would leave.
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

Resolver simulations establish the dependency plan, not installed maintainer scripts, installer behavior or a published package.

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
Write both the queue and its protection atomically, and retain every installed provider, not just the first matching alternative.
Keep a dpkg post-invoke hook that only starts the queued unit when work remains: it must reset a failed path or service after an ordinary later update, without running apt in the hook.
Bound activation of a persistent PathExists queue: a failed oneshot otherwise restarts while the file remains. One start per infinite start-limit interval, reset by the pending-work hook, leaves failure pending until a new transaction or boot. Prove that lifecycle, not just the successful worker.

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

## tasksel selection and catalogues

Keep upstream PO copies out of the Git tree: their headers can contain contacts that the edition does not republish.
Pin Debian's tasksel descriptor and archive by SHA256 and size, verify the archive against its descriptor too, and consume those exact PO members at build time.
Retain the unmodified descriptor and archive as inputs in the generated source package, with their original translator credits, so the binary rebuild can verify them and compile all ten catalogues without network.
Declare gettext in Build-Depends when the source build recompiles catalogues.
The standalone adapter normally rebuilds a resolved staging tree; retaining upstream inputs alone does not make it recompile a cached MO file.
Add a package-local catalogue build step and prove it regenerates deliberately corrupted cached MO files in an offline build.
Run publish-check on the final changed files before handing back; names stay credited and contacts stay in Debian's original source inputs.

Read the reference source's README and tests/lang: tasksel calls a Test-NAME program in /usr/lib/tasksel/tests with the task name and field arguments. Exit 0 selects a hidden task; exit 1 hides it without selecting it. A language descriptor without such a test does not automatically follow the install locale.
Use the same canonical locale mapping in tasksel and the installer. The stock base-language comparison can match both a generic language and its regional variant; test Portuguese, Spanish, Chinese and Norwegian aliases explicitly. Select only on NEW_INSTALL, preserving existing machines' choices. Require the runtime version that supplies the test program.

tasksel reads the debian-tasks gettext domain. Merge upstream's credited catalogue with the edition's messages, but put that merged payload under the edition runtime's own directory. Divert the original tasksel-data catalogue, then create a managed link in postinst; remove only that exact managed link before undoing the diversion. A preinst diversion alone does not make two different tar payloads at the same pathname acceptable to the archive gate.
Read every new title, description, installer sentence and problems-engine notice from all ten built catalogues, including the registered systemd catalogues. Exercise the real installer shell step against the target root: an intact offline image succeeds, and a negative-pinned mandatory dictionary fails with a translated explanation, the language, the missing package and a retry instruction.

English needs a task too. Debian's task-english brings locales, ibritish and iamerican; checking only application translation packs misses them. A blocked non-language base task such as task-laptop is a separate audit: compare its payload with the base selection before proposing another task.

## Qualification traps

- **Symptom:** an otherwise qualified language task branch is refused by the publication check for translator contacts in nine copied PO headers.
  **Cause:** preserved upstream credits were copied into files in our Git tree, where the edition permits names but not another person's contacts.
  **Fix:** consume checksum-pinned Debian source during preparation and retain it in the generated source package for offline catalogue compilation; remove the PO copies from Git.
  **Found by:** the changed-files publication check and a byte comparison of the old PO copies with the exact Debian archive members.
- **Symptom:** a package rebuild passes while retaining a stale compiled catalogue.
  **Cause:** the standalone source adapter copies its resolved tree without re-running the original generator.
  **Fix:** regenerate catalogues from retained, verified source inputs in the binary build and test with corrupted cached MO bytes; a missing or changed source archive must fail before compilation.
  **Found by:** reading the generated build.py and running the offline source-build control.
- **Symptom:** a replacement package silently loses files or adds unrelated payload.
  **Cause:** only its version and final success status were compared with the stage it replaces.
  **Fix:** preserve both dpkg-deb -c listings, compare every path's type, owner, mode, size, timestamp, target and content, and explain each changed listing line; separate source-date-only changes from actual content changes and control metadata.
  **Found by:** a file-by-file comparison against the previous qualified stage, required for every rebuilt package.
- **Symptom:** installed-machine tests pass, but an explicit archive smoke entry says `bwrap: execvp ...: No such file or directory` for an existing script.
  **Cause:** the archive gate resolves from an empty status database. The Locale script's Bash and the installer/selector's /bin/sh interpreter came from the installed machine's Essential baseline, not the declared closure; the merged-/usr aliases come from base-files.
  **Fix:** declare Bash for the Locale CLI and dash/base-files for the language runtime and shell helpers. Add the new entrypoints to the default lean/smoke.tsv so later publication rounds keep exercising them. Use the documented bubblewrap container flags without changing the gate's own namespace or capability isolation.
  **Found by:** the failing execution.jsonl rows, signed resolution records (no Bash in the Locale case and no dash in the installer case), then the exact interpreter and base-files symlink tar members. Runtime list and the selector input guard then start in the qualified root.
- **Symptom:** a missing dictionary makes the worker run apt repeatedly, while polling Result often shows success.
  **Cause:** PathExists remains true, and each failed five-second attempt starts again; the default start-rate limit never catches it, and Result resets during the next activation.
  **Fix:** use StartLimitIntervalSec=infinity and StartLimitBurst=1 for the service, and reset the path and service only when the next apt transaction retries pending work.
  **Found by:** the installed negative-pinned-dictionary test and repeated failed/starting entries in the real unit journal. The same test then stops with the queue and protection present and succeeds after an unrelated dictionaries-common reinstall.
- **Symptom:** the archive gate refuses different payloads at a debian-tasks.mo path although the package has a diversion.
  **Cause:** both binary tar members still claim the same pathname; a maintainer script does not change the frozen payload comparison.
  **Fix:** ship the merged catalogue at a unique path and manage the diverted-domain link during configuration and removal.
  **Found by:** the archive gate's two payload owners, followed by the binary file lists.
- **Symptom:** the queued upgrade selects Thai on a machine whose owner retained only English and Brazilian Portuguese.
  **Cause:** a shared font survived the old Locale tool's cleanup and was treated as evidence of an installed language choice.
  **Fix:** use unique non-font language packs as legacy selection evidence; retain the surviving font without using it to select a task.
  **Found by:** the old tool's installed removal plan and the queued selection on the trimmed baseline.
- **Symptom:** work stays pending after a temporary failure and a later update does not retry it.
  **Cause:** the package has not changed, so its postinst does not run again, and the path unit can be rate limited.
  **Fix:** a dpkg post-invoke hook resets and starts only the pending path/service; the service performs apt after the locks are free.
  **Found by:** following the service failure and retry lifecycle separately from package configuration.
- **Symptom:** apt update leaves a test repository's old package versions selected after its Packages file changes.
  **Cause:** a hashless Release file stayed byte-identical; apt reused the old index.
  **Fix:** regenerate Release with the Packages size and SHA256 and a valid Date whenever the local cohort changes.
  **Found by:** apt's missing-hash warning, unchanged Release and old filenames in Inst lines; this was a test repository defect.
- **Symptom:** a source rebuild fails before running debian/rules despite its explicit Build-Depends being installed.
  **Cause:** dpkg-buildpackage also requires the implicit build-essential set.
  **Fix:** use a complete build environment, then rebuild the finished source and check the resulting .buildinfo, .changes and build record for unrecorded fields.
  **Found by:** dpkg-checkbuilddeps and the build container's installed package set.
- **Symptom:** a systemd test container exits before the migration can be tested.
  **Cause:** its private cgroup tree is read-only.
  **Fix:** use the systemd rig in [shadowed-by-another-archive.md](shadowed-by-another-archive.md), with private writable cgroups, /run tmpfs and no added capability. Mask periodic apt jobs in the rig, not in the package. Prove lock waiting with a real fcntl dpkg frontend lock and capture the unit's finished journal entry.
  **Found by:** systemd's startup diagnostic and the mount options; hand-running the worker would miss hook and unit failures.

## Debian's own tasks at a tasksel transition (ORDER 756)

Symptom first: after an update the journal says `Language support could not be completed: Remv: task-laptop. Check the network and retry the update.`, `sparky-stereo-language-tasks.service` and its path unit are failed, `systemd-analyze` shows the graphical target at 1 min 32 s against 33 s the boot before, and `apt-get -s dist-upgrade` keeps `tasksel` and `tasksel-data` back.
Seen on the A10 on 2026-11-19, when Debian testing moved tasksel from 3.91 to 3.92.

- **Cause.** Every binary built from the tasksel source (`Source: tasksel`) depends on `tasksel (= its own version)`: task-laptop, task-english, the language tasks and their desktop variants.
  The edition pins Debian's `task-*` at -1, so a machine that still has them at 3.91 cannot take the 3.92 wrappers and tasksel stays back.
  The migration allowed only the language wrappers named in each language's `conflicts`; task-laptop is not a language task, so its removal was refused.
  The message said "check the network" for something that was not the network.
- **The rule the edition already had.** Debian's tasks are not the edition's (`sparky-stereo-only-ours`: "the edition's tasks are task-sparky-*"; `lists/base-gone.tsv` has task-laptop and task-english); what they brought is kept (do-not-remove-functionality).
  task-laptop has `Depends: tasksel (= 3.91)` and `Recommends: anacron, bluetooth, powertop, iw, wpasupplicant`; the Recommends were installed as automatic packages, so retiring the task alone would let `apt autoremove` take the laptop tools.
- **Fix (sparky-stereo-language-tasks 1.0.9).** `debian_tasks()` finds the installed `task-*` packages whose `Source` is tasksel (not `task-sparky-*`); the migration allows apt to remove exactly those the plan removes, marks the installed packages in their Depends and Recommends as manually installed before the install, and says what it retired and kept.
  Anything else in `Remv` still stops it, and the message names those packages (a new message, ten languages) instead of the network.
  `languages retry` (run after every dpkg transaction) queues the migration by itself when a Debian task is locked to the installed tasksel and Debian offers a newer one.
- **Rig.** `debian:testing` by digest, the edition's published tree as a `file:` source with the pins of `sparky-stereo-apt`, the 3.91 `.deb` files of tasksel, tasksel-data, task-laptop, task-english and the three Brazilian Portuguese tasks fetched from snapshot.debian.org by their SHA-1 (`/mr/binary/NAME/3.91/binfiles?fileinfo=1`, then `/file/HASH`, checked and sums recorded), installed with `apt-get install ./*.deb`, their Recommends installed and marked automatic.
  Then the published upgrade in a container with systemd as PID 1 (`--cgroupns=private --security-opt writable-cgroups=true --tmpfs /run`), judged on `apt-get -s dist-upgrade`, the journal, `systemctl --failed` and the problems engine, and a second case on a machine with no Debian task.
  The deb-multimedia source must be in the rig: the language tasks need its libdav1d7 and without it the failure is a different one.

Traps:

- **Symptom:** a failed oneshot started by a path unit stays failed with `Result=start-limit-hit`, and the next boot waits for it. **Cause:** `PathExists=` fires again as long as the file exists; the service's `StartLimitBurst=1` turns the second start into a failure, and `WantedBy=multi-user.target` makes the target wait for the whole run. **Fix:** [a queued job that fails must not loop or hold the boot](../../system-housekeeping/references/queued-job-retries-and-holds-the-boot.md).
- **Symptom:** a rig run fails with `Depends: libdav1d7 ... but it is not going to be installed`. **Cause:** the container lacks deb-multimedia. **Fix:** the keyring from the edition's tree and the source of `sparky-stereo-apt`.
- **Symptom:** `dpkg-query -W task-sparky-language-pt-br` says no packages found after a migration on a machine with no Brazilian packs. **Cause:** capture selects a language by its unique installed packs unless a retained set exists; read `pending` and `retained.json`. **Found by:** printing both files at the end of the proof.
